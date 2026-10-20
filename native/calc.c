#include <jni.h>
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "Calc.h"

#define WASM_STACK_SIZE 16
#define WASM_BYTECODE_LENGTH 6

// Real WASM opcodes: 0x20 local.get, 0x6A i32.add, 0x6B i32.sub, 0x0B end
static const unsigned char WASM_ADD_BYTECODE[] = {0x20, 0x00, 0x20, 0x01, 0x6A, 0x0B};
static const unsigned char WASM_SUB_BYTECODE[] = {0x20, 0x00, 0x20, 0x01, 0x6B, 0x0B};

static const unsigned char WASM_MUL_BYTECODE[] = {0x20, 0x00, 0x20, 0x01, 0x6C, 0x0B};
static const unsigned char WASM_DIV_BYTECODE[] = {0x20, 0x00, 0x20, 0x01, 0x6D, 0x0B};

// Cost tables. Columns: RISC-V, x86, WASM. Rows: + - * /
// Written once before any results. Do not tune them afterwards.
// Round 1: operands already in registers, count the instructions
//   RISC-V: add/sub/mul/div = 1
//   x86:    + = lea (1), - = mov+sub (2), * = mov+imul (2), / = mov+cdq+idiv (3)
//   WASM:   local.get, local.get, op = 3

static const int ROUND_1_REGISTER_COSTS[4][3] = {{1, 1, 3}, {1, 2, 3}, {1, 2, 3}, {1, 3, 3}};

// Round 2: operands in memory, result in memory, count the instructions
//   RISC-V: lw, lw, op, sw = 4
//   x86:    mov eax,[a] / op eax,[b] / mov [r],eax = 3 ( / adds cdq = 4)
//   WASM:   const, const, load, const, load, op, store = 7

static const int ROUND_2_MEMORY_COSTS[4][3] = {{4, 3, 7}, {4, 3, 7}, {4, 3, 7}, {4, 4, 7}};

static double get_current_time_in_seconds(void) {
    LARGE_INTEGER counter_frequency;
    LARGE_INTEGER counter_value;

    QueryPerformanceFrequency(&counter_frequency);
    QueryPerformanceCounter(&counter_value);

    return (double)counter_value.QuadPart / (double)counter_frequency.QuadPart;
}

// x86 add: ONE instruction (lea adds two registers into a third)
static int x86_add_two_numbers(int first_number, int second_number) {
    int result_value;

    __asm__ volatile ("leal (%q1,%q2), %0" : "=r"(result_value) : "r"(first_number), "r"(second_number));

    return result_value;
}

// x86 sub: TWO instructions (sub overwrites its destination, so copy first_number first)
static int x86_subtract_two_numbers(int first_number, int second_number) {
    int result_value;

    __asm__ volatile ("movl %1, %0\n\tsubl %2, %0" : "=&r"(result_value) : "r"(first_number), "r"(second_number));

    return result_value;
}

// x86 mul: TWO instructions (imul overwrites its destination, so copy first_number first)
static int x86_multiply_two_numbers(int first_number, int second_number) {
    int result_value;

    __asm__ volatile ("movl %1, %0\n\timull %2, %0" : "=&r"(result_value) : "r"(first_number), "r"(second_number));

    return result_value;
}

// x86 div: cltd sign-extends eax into edx, then idivl divides edx:eax
static int x86_divide_two_numbers(int first_number, int second_number) {
    int result_value;

    __asm__ volatile ("cltd\n\tidivl %2" : "=a"(result_value) : "a"(first_number), "r"(second_number) : "edx", "cc");

    return result_value;
}

static int x86_do_operation(int first_number, char operator_char, int second_number) {
    if (operator_char == '+') {
        return x86_add_two_numbers(first_number, second_number);
    }

    if (operator_char == '-') {
        return x86_subtract_two_numbers(first_number, second_number);
    }

    if (operator_char == '*') {
        return x86_multiply_two_numbers(first_number, second_number);
    }

    return x86_divide_two_numbers(first_number, second_number);
}

// Average time of one x86 operation in nanoseconds (information only)
static double measure_x86_nanoseconds_per_operation(int first_number, char operator_char, int second_number) {
    volatile int volatile_first_number  = first_number;
    volatile int volatile_second_number = second_number;
    volatile int sink_value             = 0;
    const int NUMBER_OF_ITERATIONS      = 1000000;

    double start_time = get_current_time_in_seconds();

    for (int loop_index = 0; loop_index < NUMBER_OF_ITERATIONS; loop_index = loop_index + 1) {
        sink_value = x86_do_operation(volatile_first_number, operator_char, volatile_second_number);
    }

    double end_time = get_current_time_in_seconds();

    (void)sink_value;
    return (end_time - start_time) * 1e9 / NUMBER_OF_ITERATIONS;
}

// WASM worker (a tiny stack machine)
// Returns 1 on success and sets *result_value
// *instruction_count = instructions executed (the final 'end' is not counted)
static int wasm_run_bytecode(const unsigned char *bytecode, int bytecode_length, int first_number, int second_number, int *result_value, int *instruction_count) {
    int local_variables[2] = {first_number, second_number};
    int value_stack[WASM_STACK_SIZE];
    int stack_pointer      = 0;
    int program_counter    = 0;
    *instruction_count     = 0;

    while (program_counter < bytecode_length) {
        unsigned char current_opcode = bytecode[program_counter];
        program_counter = program_counter + 1;

        // end: exactly one value must remain
        if (current_opcode == 0x0B) {
            if (stack_pointer != 1) {
                return 0;
            }
            *result_value = value_stack[0];
            return 1;
        }

        *instruction_count = *instruction_count + 1;

        // local.get index: push a local
        if (current_opcode == 0x20) {
            if (program_counter >= bytecode_length) {
                return 0;
            }
            int local_index = bytecode[program_counter];
            program_counter = program_counter + 1;

            if (local_index > 1 || stack_pointer >= WASM_STACK_SIZE) {
                return 0;
            }
            value_stack[stack_pointer] = local_variables[local_index];
            stack_pointer = stack_pointer + 1;
        }
        // i32.add / i32.sub / i32.mul / i32.div: pop two, push one
        else if (current_opcode == 0x6A || current_opcode == 0x6B || current_opcode == 0x6C || current_opcode == 0x6D) {
            if (stack_pointer < 2) {
                return 0;
            }
            stack_pointer = stack_pointer - 1;
            unsigned int right_operand = (unsigned int)value_stack[stack_pointer];
            stack_pointer = stack_pointer - 1;
            unsigned int left_operand  = (unsigned int)value_stack[stack_pointer];

            if (current_opcode == 0x6A) {
                value_stack[stack_pointer] = (int)(left_operand + right_operand);
            }
            else if (current_opcode == 0x6B) {
                value_stack[stack_pointer] = (int)(left_operand - right_operand);
            }
            else if (current_opcode == 0x6C) {
                value_stack[stack_pointer] = (int)(left_operand * right_operand);
            }
            else {
                // div_s traps on divide by zero and on INT_MIN / -1
                if ((int)right_operand == 0 || ((int)left_operand == INT_MIN && (int)right_operand == -1)) {
                    return 0;
                }
                value_stack[stack_pointer] = (int)left_operand / (int)right_operand;
            }
            stack_pointer = stack_pointer + 1;
        }
        else {
            // unknown opcode
            return 0;
        }
    }

    // ran off the end without 'end'
    return 0;
}

// Writes the instructions that put value_to_load into register_name. Returns how many it wrote
static int write_instructions_to_load_value_into_register(FILE *assembly_file, const char *register_name, int value_to_load) {
    if (value_to_load >= -2048 && value_to_load <= 2047) {
        fprintf(assembly_file, "addi %s, zero, %d\n", register_name, value_to_load);
        return 1;
    }

    int lower_12_bits = ((value_to_load & 0xFFF) ^ 0x800) - 0x800;
    int upper_20_bits = (int)(((unsigned int)value_to_load - (unsigned int)lower_12_bits) >> 12);

    if (upper_20_bits >= 524288) {
        upper_20_bits = upper_20_bits - 1048576;
    }

    fprintf(assembly_file, "lui %s, %d\n", register_name, upper_20_bits);

    if (lower_12_bits != 0) {
        fprintf(assembly_file, "addi %s, %s, %d\n", register_name, register_name, lower_12_bits);
        return 2;
    }

    return 1;
}

// mnemonic is "add" or "sub". Returns 1 on success
// *core_instruction_count = instructions the simulator ran for the operation itself,
// with the setup (loading the two numbers) subtracted
static int riscv_run_operation(const char *mnemonic, int first_number, int second_number, int *result_value, int *core_instruction_count) {
    FILE *assembly_file = fopen("riscv\\add.s", "w");
    if (assembly_file == NULL) {
        return 0;
    }

    int setup_instruction_count = 0;
    setup_instruction_count = setup_instruction_count + write_instructions_to_load_value_into_register(assembly_file, "a0", first_number);
    setup_instruction_count = setup_instruction_count + write_instructions_to_load_value_into_register(assembly_file, "a1", second_number);
    fprintf(assembly_file, "%s a2, a0, a1\n", mnemonic);
    fclose(assembly_file);

    if (system("py riscv\\run.py riscv\\add.s riscv\\add.txt riscv\\trace.txt > nul") != 0) {
        return 0;
    }

    FILE *trace_file = fopen("riscv\\trace.txt", "r");
    if (trace_file == NULL) {
        return 0;
    }

    char current_line[4096];
    char last_line[4096] = "";
    int total_instruction_count = 0;

    while (fgets(current_line, sizeof current_line, trace_file) != NULL) {
        strcpy(last_line, current_line);
        // one line per executed instruction
        total_instruction_count = total_instruction_count + 1;
    }
    fclose(trace_file);

    *core_instruction_count = total_instruction_count - setup_instruction_count;

    char *token = strtok(last_line, " \r\n");
    for (int token_index = 0; token_index < 13; token_index = token_index + 1) {
        token = strtok(NULL, " \r\n");
        if (token == NULL) {
            return 0;
        }
    }

    unsigned long raw_register_value = strtoul(token + 2, NULL, 2);
    *result_value = (int)(unsigned int)raw_register_value;
    return 1;
}

static int get_operator_row_index(char operator_char) {
    if (operator_char == '+') {
        return 0;
    }

    if (operator_char == '-') {
        return 1;
    }

    if (operator_char == '*') {
        return 2;
    }

    return 3;
}

// Signed LEB128 length: how many bytes WASM needs to encode this constant
static int count_signed_leb128_bytes(int value) {
    if (value >= -64 && value <= 63) {
        return 1;
    }

    if (value >= -8192 && value <= 8191) {
        return 2;
    }

    if (value >= -1048576 && value <= 1048575) {
        return 3;
    }

    if (value >= -134217728 && value <= 134217727) {
        return 4;
    }

    return 5;
}

// RISC-V: one addi (4 bytes), or lui+addi (8 bytes), or lui alone when the low 12 bits are zero
static int count_riscv_load_bytes(int value) {
    if (value >= -2048 && value <= 2047) {
        return 4;
    }

    if ((value & 0xFFF) == 0) {
        return 4;
    }

    return 8;
}

// Round 3: bytes of code needed to compute the result from two constants
// RISC-V: load a, load b, one operation instruction of 4 bytes
static int count_riscv_code_bytes(int first_number, int second_number) {
    return count_riscv_load_bytes(first_number) + count_riscv_load_bytes(second_number) + 4;
}

// x86: mov eax,imm32 (5 bytes), then + - use add/sub eax,imm8 (3) or imm32 (5),
// * uses imul eax,eax,imm8 (3) or imm32 (6), / uses cdq (1) + mov ecx,imm32 (5) + idiv ecx (2)
static int count_x86_code_bytes(char operator_char, int second_number) {
    int second_number_fits_in_one_byte = (second_number >= -128 && second_number <= 127);

    if (operator_char == '/') {
        return 13;
    }

    if (operator_char == '*') {
        if (second_number_fits_in_one_byte) {
            return 5 + 3;
        }
        return 5 + 6;
    }

    if (second_number_fits_in_one_byte) {
        return 5 + 3;
    }
    return 5 + 5;
}

// WASM: i32.const a, i32.const b, op (the 'end' byte is not counted)
static int count_wasm_code_bytes(int first_number, int second_number) {
    return (1 + count_signed_leb128_bytes(first_number)) + (1 + count_signed_leb128_bytes(second_number)) + 1;
}

// Fills verdict_text (needs 64 chars) with the winner(s) of one round. Fewest wins, ties share the win
static void build_round_verdict_text(const int round_scores[3], char *verdict_text) {
    const char *machine_names[3] = {"RISC-V", "x86", "WASM"};
    int fewest_score             = round_scores[0];

    for (int machine_index = 1; machine_index < 3; machine_index = machine_index + 1) {
        if (round_scores[machine_index] < fewest_score) {
            fewest_score = round_scores[machine_index];
        }
    }

    verdict_text[0] = '\0';
    int number_of_winners = 0;

    for (int machine_index = 0; machine_index < 3; machine_index = machine_index + 1) {
        if (round_scores[machine_index] == fewest_score) {
            if (number_of_winners > 0) {
                strcat(verdict_text, " & ");
            }
            strcat(verdict_text, machine_names[machine_index]);
            number_of_winners = number_of_winners + 1;
        }
    }

    if (number_of_winners == 3) {
        strcpy(verdict_text, "3-way TIE");
    }
    else if (number_of_winners == 1) {
        strcat(verdict_text, " wins");
    }
    else {
        strcat(verdict_text, " tie for first");
    }
}

static int race_all_three_machines(JNIEnv *java_env, jclass java_class, int first_number, char operator_char, int second_number) {
    const char *operation_name;
    int plain_c_result;

    if (operator_char == '+') {
        operation_name = "add";
        plain_c_result = (int)((unsigned int)first_number + (unsigned int)second_number);
    }
    else if (operator_char == '-') {
        operation_name = "sub";
        plain_c_result = (int)((unsigned int)first_number - (unsigned int)second_number);
    }
    else if (operator_char == '*') {
        operation_name = "mul";
        plain_c_result = (int)((unsigned int)first_number * (unsigned int)second_number);
    }
    else {
        operation_name = "div";
        plain_c_result = first_number / second_number;
    }

    // Java referee (subtraction only): Java's sub must agree too
    int java_was_checked = 0;
    int java_result      = plain_c_result;

    if (operator_char == '-') {
        jmethodID java_sub_method_id = (*java_env)->GetStaticMethodID(java_env, java_class, "sub", "(II)I");
        if (java_sub_method_id != NULL) {
            java_result      = (*java_env)->CallStaticIntMethod(java_env, java_class, java_sub_method_id, first_number, second_number);
            java_was_checked = 1;
        }
    }

    double riscv_start_time = get_current_time_in_seconds();
    int riscv_result                 = 0;
    int riscv_core_instruction_count = 0;
    int riscv_succeeded = riscv_run_operation(operation_name, first_number, second_number, &riscv_result, &riscv_core_instruction_count);
    double riscv_time_in_milliseconds = (get_current_time_in_seconds() - riscv_start_time) * 1000.0;

    if (!riscv_succeeded) {
        fprintf(stderr, "[riscv failed, using plain C]\n");
        return plain_c_result;
    }

    int x86_result = x86_do_operation(first_number, operator_char, second_number);

    int wasm_result                 = 0;
    int wasm_core_instruction_count = 0;
    const unsigned char *wasm_bytecode;

    if (operator_char == '+') {
        wasm_bytecode = WASM_ADD_BYTECODE;
    }
    else if (operator_char == '-') {
        wasm_bytecode = WASM_SUB_BYTECODE;
    }
    else if (operator_char == '*') {
        wasm_bytecode = WASM_MUL_BYTECODE;
    }
    else {
        wasm_bytecode = WASM_DIV_BYTECODE;
    }

    if (!wasm_run_bytecode(wasm_bytecode, WASM_BYTECODE_LENGTH, first_number, second_number, &wasm_result, &wasm_core_instruction_count)) {
        fprintf(stderr, "[wasm failed, using plain C]\n");
        return plain_c_result;
    }

    if (x86_result != riscv_result || riscv_result != plain_c_result || wasm_result != riscv_result || (java_was_checked && java_result != riscv_result)) {
        fprintf(stderr, "[MISMATCH: riscv=%d x86=%d wasm=%d plain=%d java=%d, using plain C]\n", riscv_result, x86_result, wasm_result, plain_c_result, java_result);
        return plain_c_result;
    }

    double x86_nanoseconds_per_operation = measure_x86_nanoseconds_per_operation(first_number, operator_char, second_number);
    int operator_row_index = get_operator_row_index(operator_char);
    int round_3_scores[3]  = {count_riscv_code_bytes(first_number, second_number), count_x86_code_bytes(operator_char, second_number), count_wasm_code_bytes(first_number, second_number)};

    char round_1_verdict_text[64];
    char round_2_verdict_text[64];
    char round_3_verdict_text[64];

    build_round_verdict_text(ROUND_1_REGISTER_COSTS[operator_row_index], round_1_verdict_text);
    build_round_verdict_text(ROUND_2_MEMORY_COSTS[operator_row_index], round_2_verdict_text);
    build_round_verdict_text(round_3_scores, round_3_verdict_text);

    fprintf(stderr, "  %s:\n", operation_name);
    fprintf(stderr, "    Round 1 (operands in registers, instructions): RISC-V %d | x86 %d | WASM %d -> %s\n", ROUND_1_REGISTER_COSTS[operator_row_index][0], ROUND_1_REGISTER_COSTS[operator_row_index][1], ROUND_1_REGISTER_COSTS[operator_row_index][2], round_1_verdict_text);
    fprintf(stderr, "    Round 2 (memory in, memory out, instructions): RISC-V %d | x86 %d | WASM %d -> %s\n", ROUND_2_MEMORY_COSTS[operator_row_index][0], ROUND_2_MEMORY_COSTS[operator_row_index][1], ROUND_2_MEMORY_COSTS[operator_row_index][2], round_2_verdict_text);
    fprintf(stderr, "    Round 3 (constants, bytes of code): RISC-V %d | x86 %d | WASM %d -> %s\n", round_3_scores[0], round_3_scores[1], round_3_scores[2], round_3_verdict_text);

    if (java_was_checked) {
        fprintf(stderr, "  Java referee agrees: %d\n", java_result);
    }

    fprintf(stderr, "  (info only, not judged: RISC-V sim round trip %.0f ms, x86 native %.1f ns)\n", riscv_time_in_milliseconds, x86_nanoseconds_per_operation);

    return riscv_result;
}

JNIEXPORT jint JNICALL Java_Calc_calculate(JNIEnv *java_env, jclass java_class, jint first_number, jchar operator_char, jint second_number)
{
    if (operator_char != '+' && operator_char != '-' && operator_char != '*' && operator_char != '/') {
        return 0;
    }

    // safety net: idiv crashes on these (Java already checks them first)
    if (operator_char == '/' && (second_number == 0 || (first_number == INT_MIN && second_number == -1))) {
        return 0;
    }

    if (getenv("CALC_FAST") == NULL) {
        return race_all_three_machines(java_env, java_class, first_number, (char)operator_char, second_number);
    }

    // fast mode: skip the race
    if (operator_char == '+') {
        return first_number + second_number;
    }

    if (operator_char == '*') {
        return (int)((unsigned int)first_number * (unsigned int)second_number);
    }

    if (operator_char == '/') {
        return first_number / second_number;
    }

    jmethodID java_sub_method_id = (*java_env)->GetStaticMethodID(java_env, java_class, "sub", "(II)I");
    if (java_sub_method_id == NULL) {
        return -1;
    }

    return (*java_env)->CallStaticIntMethod(java_env, java_class, java_sub_method_id, first_number, second_number);
}