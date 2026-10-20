import sys


registers_state_of_all = [0] * 32
registers_state_of_all[2] = 0x0000017C

memory = {}
for i in range(64):
    memory[0x00000000 + i * 4] = 0
for i in range(32):
    memory[0x00000100 + i * 4] = 0
for i in range(32):
    memory[0x00010000 + i * 4] = 0

program_counter = 0

instructions = []

with open(sys.argv[1], 'r') as f:
    for line in f:
        instructions.append(line.strip())

def integer_ko_bnaao_to_binary_32(numberrrr):
    if numberrrr < 0:
        numberrrr = numberrrr + (1 << 32)
    return "0b" + format(numberrrr, '032b')

output_lines = []

def sign_extend_12(imm):
    if imm & (1 << 11):
        imm -= (1 << 12)
    return imm

def to_signed_32(value):
    if value < (1 << 31):
        return value
    return value - (1 << 32)

def save_register_state(program_counter, registers_state_of_all, output_lines):
    pc_byte_address = program_counter * 4
    line = integer_ko_bnaao_to_binary_32(pc_byte_address)
    for i in range(32):
        line = line + " " + integer_ko_bnaao_to_binary_32(registers_state_of_all[i])
    output_lines.append(line)
    return output_lines

def save_memory_state(output_lines):
    for i in range(32):
        address_values = 0x00010000 + i * 4
        values_in_addresss = memory.get(address_values, 0)
        if values_in_addresss < 0:
            values_in_addresss = values_in_addresss + (1 << 32)
        address_in_hex = "0x" + format(address_values, '08X')
        value_in_binary = integer_ko_bnaao_to_binary_32(values_in_addresss)
        output_lines.append(address_in_hex + ":" + value_in_binary)
    uart_val = memory.get(0x10000000, 0)
    output_lines.append("0x10000000:" + integer_ko_bnaao_to_binary_32(uart_val))
    return output_lines

def write_output_and_stop():
    with open(sys.argv[2], 'w') as f:
        for line in output_lines:
            f.write(line + "\n")
    sys.exit(0)

def is_valid_memory_address(address):
    if address == 0x10000000:
        return True
    if 0x00000000 <= address <= 0x000000FF:
        return True
    if 0x00000100 <= address <= 0x0000017F:
        return True
    if 0x00010000 <= address <= 0x0001007F:
        return True
    return False

def branch_taken(immediate_actually_used):
    global program_counter, output_lines
    registers_state_of_all[0] = 0
    program_counter += immediate_actually_used // 4
    if program_counter < 0 or program_counter >= len(instructions):
        write_output_and_stop()
    output_lines = save_register_state(program_counter, registers_state_of_all, output_lines)

while program_counter < len(instructions):
    instruction_jo_execute_krna_hai_1_1_krke = instructions[program_counter]
    opcode = instruction_jo_execute_krna_hai_1_1_krke[25:32]

    if opcode == "0110011":
        rd     = int(instruction_jo_execute_krna_hai_1_1_krke[20:25], 2)
        rs1    = int(instruction_jo_execute_krna_hai_1_1_krke[12:17], 2)
        rs2    = int(instruction_jo_execute_krna_hai_1_1_krke[7:12],  2)
        funct3 = instruction_jo_execute_krna_hai_1_1_krke[17:20]
        funct7 = instruction_jo_execute_krna_hai_1_1_krke[0:7]
        value_in_rs1 = registers_state_of_all[rs1]
        value_in_rs2 = registers_state_of_all[rs2]

        if funct3 == "000" and funct7 == "0000000":
            if rd != 0:
                registers_state_of_all[rd] = (value_in_rs1 + value_in_rs2) & 0xFFFFFFFF
        elif funct3 == "000" and funct7 == "0100000":
            if rd != 0:
                registers_state_of_all[rd] = (value_in_rs1 - value_in_rs2) & 0xFFFFFFFF
        elif funct3 == "000" and funct7 == "0000001":
            if rd != 0:
                registers_state_of_all[rd] = (to_signed_32(value_in_rs1) * to_signed_32(value_in_rs2)) & 0xFFFFFFFF
        elif funct3 == "100" and funct7 == "0000001":
            if rd != 0:
                divisor = to_signed_32(value_in_rs2)
                if divisor == 0:
                    registers_state_of_all[rd] = 0xFFFFFFFF
                else:
                    registers_state_of_all[rd] = int(to_signed_32(value_in_rs1) / divisor) & 0xFFFFFFFF
        elif funct3 == "001" and funct7 == "0000000":
            if rd != 0:
                registers_state_of_all[rd] = (value_in_rs1 << (value_in_rs2 & 0b11111)) & 0xFFFFFFFF
        elif funct3 == "010" and funct7 == "0000000":
            if rd != 0:
                if to_signed_32(value_in_rs1) < to_signed_32(value_in_rs2):
                    registers_state_of_all[rd] = 1
                else:
                    registers_state_of_all[rd] = 0
        elif funct3 == "011" and funct7 == "0000000":
            if rd != 0:
                if (value_in_rs1 & 0xFFFFFFFF) < (value_in_rs2 & 0xFFFFFFFF):
                    registers_state_of_all[rd] = 1
                else:
                    registers_state_of_all[rd] = 0
        elif funct3 == "100" and funct7 == "0000000":
            if rd != 0:
                registers_state_of_all[rd] = (value_in_rs1 ^ value_in_rs2) & 0xFFFFFFFF
        elif funct3 == "101" and funct7 == "0000000":
            if rd != 0:
                registers_state_of_all[rd] = ((value_in_rs1 & 0xFFFFFFFF) >> (value_in_rs2 & 0b11111)) & 0xFFFFFFFF
        elif funct3 == "110" and funct7 == "0000000":
            if rd != 0:
                registers_state_of_all[rd] = (value_in_rs1 | value_in_rs2) & 0xFFFFFFFF
        elif funct3 == "111" and funct7 == "0000000":
            if rd != 0:
                registers_state_of_all[rd] = (value_in_rs1 & value_in_rs2) & 0xFFFFFFFF

    elif opcode == "0000011":
        rd     = int(instruction_jo_execute_krna_hai_1_1_krke[20:25], 2)
        rs1    = int(instruction_jo_execute_krna_hai_1_1_krke[12:17], 2)
        funct3 = instruction_jo_execute_krna_hai_1_1_krke[17:20]
        imm    = sign_extend_12(int(instruction_jo_execute_krna_hai_1_1_krke[0:12], 2))
        rs1_ki_value = registers_state_of_all[rs1]
        address_jaha_se_load_karna_hain = rs1_ki_value + imm
        if address_jaha_se_load_karna_hain % 4 != 0:
            print("ERROR: Unaligned LOAD at address", hex(address_jaha_se_load_karna_hain))
            write_output_and_stop()
        if not is_valid_memory_address(address_jaha_se_load_karna_hain):
            print("ERROR: Invalid LOAD at address", hex(address_jaha_se_load_karna_hain))
            write_output_and_stop()
        if rd != 0:
            registers_state_of_all[rd] = memory.get(address_jaha_se_load_karna_hain, 0) & 0xFFFFFFFF

    elif opcode == "0100011":
        rs1    = int(instruction_jo_execute_krna_hai_1_1_krke[12:17], 2)
        rs2    = int(instruction_jo_execute_krna_hai_1_1_krke[7:12],  2)
        funct3 = instruction_jo_execute_krna_hai_1_1_krke[17:20]
        imm    = sign_extend_12(int(instruction_jo_execute_krna_hai_1_1_krke[0:7] + instruction_jo_execute_krna_hai_1_1_krke[20:25], 2))
        rs1_ki_value = registers_state_of_all[rs1]
        rs2_ki_value = registers_state_of_all[rs2]
        address_jahan_store_karna_hain = rs1_ki_value + imm

        if funct3 == "010":  # sw
            if address_jahan_store_karna_hain % 4 != 0:
                print("ERROR: Unaligned STORE at address", hex(address_jahan_store_karna_hain))
                write_output_and_stop()
            if not is_valid_memory_address(address_jahan_store_karna_hain):
                print("ERROR: Invalid STORE at address", hex(address_jahan_store_karna_hain))
                write_output_and_stop()
            memory[address_jahan_store_karna_hain] = rs2_ki_value & 0xFFFFFFFF
        elif funct3 == "000":  # sb
            aligned = address_jahan_store_karna_hain & ~3
            if not is_valid_memory_address(aligned):
                print("ERROR: Invalid SB at address", hex(address_jahan_store_karna_hain))
                write_output_and_stop()
            byte_offset = address_jahan_store_karna_hain & 3
            old = memory.get(aligned, 0)
            byte_val = rs2_ki_value & 0xFF
            shift = byte_offset * 8
            new = (old & ~(0xFF << shift)) | (byte_val << shift)
            memory[aligned] = new

    elif opcode == "0010011":
        rd     = int(instruction_jo_execute_krna_hai_1_1_krke[20:25], 2)
        rs1    = int(instruction_jo_execute_krna_hai_1_1_krke[12:17], 2)
        funct3 = instruction_jo_execute_krna_hai_1_1_krke[17:20]
        imm    = sign_extend_12(int(instruction_jo_execute_krna_hai_1_1_krke[0:12], 2))
        rs1_ki_value = registers_state_of_all[rs1]
        if funct3 == "000":
            if rd != 0:
                registers_state_of_all[rd] = (rs1_ki_value + imm) & 0xFFFFFFFF
        elif funct3 == "011":
            if rd != 0:
                if (rs1_ki_value & 0xFFFFFFFF) < (imm & 0xFFFFFFFF):
                    registers_state_of_all[rd] = 1
                else:
                    registers_state_of_all[rd] = 0

    elif opcode == "1100111":
        rd     = int(instruction_jo_execute_krna_hai_1_1_krke[20:25], 2)
        rs1    = int(instruction_jo_execute_krna_hai_1_1_krke[12:17], 2)
        funct3 = instruction_jo_execute_krna_hai_1_1_krke[17:20]
        imm    = sign_extend_12(int(instruction_jo_execute_krna_hai_1_1_krke[0:12], 2))
        rs1_ki_value = registers_state_of_all[rs1]
        if rd != 0:
            registers_state_of_all[rd] = ((program_counter + 1) * 4) & 0xFFFFFFFF
        registers_state_of_all[0] = 0
        target = (rs1_ki_value + imm) & ~1
        if target % 4 != 0:
            print("ERROR: Unaligned JALR")
            write_output_and_stop()
        program_counter = target // 4
        if program_counter < 0 or program_counter >= len(instructions):
            write_output_and_stop()
        output_lines = save_register_state(program_counter, registers_state_of_all, output_lines)
        continue

    elif opcode == "1100011":
        funct3 = instruction_jo_execute_krna_hai_1_1_krke[17:20]
        rs1    = int(instruction_jo_execute_krna_hai_1_1_krke[12:17], 2)
        rs2    = int(instruction_jo_execute_krna_hai_1_1_krke[7:12],  2)
        actual_immediate = (instruction_jo_execute_krna_hai_1_1_krke[0] +
                            instruction_jo_execute_krna_hai_1_1_krke[24] +
                            instruction_jo_execute_krna_hai_1_1_krke[1:7] +
                            instruction_jo_execute_krna_hai_1_1_krke[20:24] + "0")
        if actual_immediate[0] == '1':
            immediate_actually_used = int(actual_immediate, 2) - (1 << 13)
        else:
            immediate_actually_used = int(actual_immediate, 2)
        value_in_rs1 = registers_state_of_all[rs1]
        value_in_rs2 = registers_state_of_all[rs2]

        if funct3 == "000":
            if value_in_rs1 == value_in_rs2:
                branch_taken(immediate_actually_used)
                continue
        elif funct3 == "001":
            if value_in_rs1 != value_in_rs2:
                branch_taken(immediate_actually_used)
                continue
        elif funct3 == "100":
            if to_signed_32(value_in_rs1) < to_signed_32(value_in_rs2):
                branch_taken(immediate_actually_used)
                continue
        elif funct3 == "101":
            if to_signed_32(value_in_rs1) >= to_signed_32(value_in_rs2):
                branch_taken(immediate_actually_used)
                continue
        elif funct3 == "110":
            if (value_in_rs1 & 0xFFFFFFFF) < (value_in_rs2 & 0xFFFFFFFF):
                branch_taken(immediate_actually_used)
                continue
        elif funct3 == "111":
            if (value_in_rs1 & 0xFFFFFFFF) >= (value_in_rs2 & 0xFFFFFFFF):
                branch_taken(immediate_actually_used)
                continue

    elif opcode == "0110111":
        rd = int(instruction_jo_execute_krna_hai_1_1_krke[20:25], 2)
        immediate_needed_to_extended = int(instruction_jo_execute_krna_hai_1_1_krke[0:20], 2)
        extended_immediate = immediate_needed_to_extended << 12
        if rd != 0:
            registers_state_of_all[rd] = extended_immediate & 0xFFFFFFFF

    elif opcode == "0010111":
        rd = int(instruction_jo_execute_krna_hai_1_1_krke[20:25], 2)
        immediate_needed_to_extended = int(instruction_jo_execute_krna_hai_1_1_krke[0:20], 2)
        extended_immediate = immediate_needed_to_extended << 12
        needed_pc_to_be_added_in_U = program_counter * 4
        if rd != 0:
            registers_state_of_all[rd] = (needed_pc_to_be_added_in_U + extended_immediate) & 0xFFFFFFFF

    elif opcode == "1101111":
        rd = int(instruction_jo_execute_krna_hai_1_1_krke[20:25], 2)
        immediate_part_1 = instruction_jo_execute_krna_hai_1_1_krke[0]
        immediate_part_2 = instruction_jo_execute_krna_hai_1_1_krke[1:11]
        immediate_part_3 = instruction_jo_execute_krna_hai_1_1_krke[11]
        immediate_part_4 = instruction_jo_execute_krna_hai_1_1_krke[12:20]
        immediate_actually_used = immediate_part_1 + immediate_part_4 + immediate_part_3 + immediate_part_2 + "0"
        immediate_actually_used_in_binary = int(immediate_actually_used, 2)
        if immediate_actually_used[0] == "1":
            immediate_actually_used_in_binary = immediate_actually_used_in_binary - (1 << 21)
        if rd != 0:
            registers_state_of_all[rd] = ((program_counter + 1) * 4) & 0xFFFFFFFF
        registers_state_of_all[0] = 0
        program_counter += immediate_actually_used_in_binary // 4
        if program_counter < 0 or program_counter >= len(instructions):
            write_output_and_stop()
        if immediate_actually_used_in_binary == 0 and rd == 0:
            output_lines = save_register_state(program_counter, registers_state_of_all, output_lines)
            output_lines = save_memory_state(output_lines)
            write_output_and_stop()
        output_lines = save_register_state(program_counter, registers_state_of_all, output_lines)
        continue

    registers_state_of_all[0] = 0
    program_counter += 1
    output_lines = save_register_state(program_counter, registers_state_of_all, output_lines)

write_output_and_stop()