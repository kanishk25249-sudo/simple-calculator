import sys
R_TYPE={
    "add":  {"funct3": "000", "funct7": "0000000", "opcode": "0110011"},
    "sub":  {"funct3": "000", "funct7": "0100000", "opcode": "0110011"},
    "sll":  {"funct3": "001", "funct7": "0000000", "opcode": "0110011"},
    "slt":  {"funct3": "010", "funct7": "0000000", "opcode": "0110011"},
    "sltu": {"funct3": "011", "funct7": "0000000", "opcode": "0110011"},
    "xor":  {"funct3": "100", "funct7": "0000000", "opcode": "0110011"},
    "srl":  {"funct3": "101", "funct7": "0000000", "opcode": "0110011"},
    "or":   {"funct3": "110", "funct7": "0000000", "opcode": "0110011"},
    "and":  {"funct3": "111", "funct7": "0000000", "opcode": "0110011"},
    "mul":  {"funct3": "000", "funct7": "0000001", "opcode": "0110011"},
    "div":  {"funct3": "100", "funct7": "0000001", "opcode": "0110011"}
}

I_TYPE = {
    "lw":    {"funct3": "010", "opcode": "0000011"},
    "addi":  {"funct3": "000", "opcode": "0010011"},
    "sltiu": {"funct3": "011", "opcode": "0010011"},
    "jalr":  {"funct3": "000", "opcode": "1100111"}
}

S_TYPE = {
    "sw": {"funct3": "010", "opcode": "0100011"},
    "sb": {"funct3": "000", "opcode": "0100011"}
}

REGISTER_MAP = {
  
"zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011",

"tp": "00100", "t0": "00101", "t1": "00110", "t2": "00111",

"s0": "01000", "fp": "01000", "s1": "01001", "a0": "01010",

"a1": "01011", "a2": "01100", "a3": "01101", "a4": "01110",

"a5": "01111", "a6": "10000", "a7": "10001", "s2": "10010",

"s3": "10011", "s4": "10100", "s5": "10101", "s6": "10110",

"s7": "10111", "s8": "11000", "s9": "11001", "s10": "11010",

"s11": "11011", "t3": "11100", "t4": "11101", "t5": "11110",

"t6": "11111",
  

"x0": "00000", "x1": "00001", "x2": "00010", "x3": "00011",

"x4": "00100", "x5": "00101", "x6": "00110", "x7": "00111",

"x8": "01000", "x9": "01001", "x10": "01010", "x11": "01011",

"x12": "01100", "x13": "01101", "x14": "01110", "x15": "01111",

"x16": "10000", "x17": "10001", "x18": "10010", "x19": "10011",

"x20": "10100", "x21": "10101", "x22": "10110", "x23": "10111",

"x24": "11000", "x25": "11001", "x26": "11010", "x27": "11011",

"x28": "11100", "x29": "11101", "x30": "11110", "x31": "11111"

}

def get_binary_number_of_register_from_register_name(name_reg, line_num):
    reg_number = REGISTER_MAP.get(name_reg)
    if reg_number is None:
        print(f"Error at line {line_num}: Invalid register name '{name_reg}'")
        sys.exit(1)
    return reg_number
  
def find_all_labels(lines):
  labels = {}
  count = 0

  for line in lines:
      line = line.strip()          

      if "#" in line:
          line = line.split("#")[0]
      if line == "":
          continue

      if ":" in line:
          parts = line.split(":")  
          name = parts[0].strip()  
          labels[name] = count * 4

          if parts[1].strip() != "":
              count = count + 1
      else:
          count = count + 1

  return labels

def number_to_binary(num, num_of_bits, line_num):
    minimum_kahan_tk_jaa_skta_hai_num = -(2 ** (num_of_bits - 1))
    maximum_kahan_tk_jaa_skta_hai_num =  (2 ** (num_of_bits - 1)) - 1

    if num < minimum_kahan_tk_jaa_skta_hai_num or num > maximum_kahan_tk_jaa_skta_hai_num:
        print(f"Error at line {line_num}: Immediate {num} out of range ({minimum_kahan_tk_jaa_skta_hai_num} to {maximum_kahan_tk_jaa_skta_hai_num})")
        sys.exit(1)

    masked = num & ((2 ** num_of_bits) - 1)
    return format(masked, f'0{num_of_bits}b')

def parse_immediate_value(numberrrrr, line_num):
    numberrrrr = numberrrrr.strip()
    try:
        return int(numberrrrr, 0)
    except ValueError:
        print(f"Error at line {line_num}: '{numberrrrr}' is not a valid number")
        sys.exit(1)

def parse_instruction(line):
    line = line.strip()
    if len(line) == 0:
        return None, None
    line = line.replace(",", " ")
    parts = line.split()
    opcode = parts[0].lower()
    operands = parts[1:]
    return opcode, operands

def encode_r_type(opcode, operands, line_num):
    if len(operands) != 3:
        print(f"Error at line {line_num}: {opcode} needs exactly 3 registers")
        sys.exit(1)
    rd  = get_binary_number_of_register_from_register_name(operands[0], line_num)
    rs1 = get_binary_number_of_register_from_register_name(operands[1], line_num)
    rs2 = get_binary_number_of_register_from_register_name(operands[2], line_num)

    opcode_bits = R_TYPE[opcode]["opcode"]
    funct3      = R_TYPE[opcode]["funct3"]
    funct7      = R_TYPE[opcode]["funct7"]

    return funct7 + rs2 + rs1 + funct3 + rd + opcode_bits

def encode_i_type(opcode, operands, line_num):

    if opcode == "lw":
        if operands[0] not in REGISTER_MAP:
            print(f"Error at line {line_num}: Invalid register '{operands[0]}'")
            sys.exit(1)
        rd_name  = operands[0]
        imm_part = operands[1].split("(")[0]
        rs1_name = operands[1].split("(")[1].split(")")[0]
        if rs1_name not in REGISTER_MAP:
            print(f"Error at line {line_num}: Invalid register '{rs1_name}'")
            sys.exit(1)
        rd  = get_binary_number_of_register_from_register_name(rd_name, line_num)
        rs1 = get_binary_number_of_register_from_register_name(rs1_name, line_num)
        imm = parse_immediate_value(imm_part, line_num)

    elif opcode == "jalr" and "(" in operands[1]:
        if operands[0] not in REGISTER_MAP:
            print(f"Error at line {line_num}: Invalid register '{operands[0]}'")
            sys.exit(1)
        rd_name  = operands[0]
        imm_part = operands[1].split("(")[0]
        rs1_name = operands[1].split("(")[1].split(")")[0]
        if rs1_name not in REGISTER_MAP:
            print(f"Error at line {line_num}: Invalid register '{rs1_name}'")
            sys.exit(1)
        rd  = get_binary_number_of_register_from_register_name(rd_name, line_num)
        rs1 = get_binary_number_of_register_from_register_name(rs1_name, line_num)
        imm = parse_immediate_value(imm_part, line_num)

    else:
        if operands[0] not in REGISTER_MAP:
            print(f"Error at line {line_num}: Invalid register '{operands[0]}'")
            sys.exit(1)
        if operands[1] not in REGISTER_MAP:
            print(f"Error at line {line_num}: Invalid register '{operands[1]}'")
            sys.exit(1)
        rd_name  = operands[0]
        rs1_name = operands[1]
        rd  = get_binary_number_of_register_from_register_name(rd_name, line_num)
        rs1 = get_binary_number_of_register_from_register_name(rs1_name, line_num)
        imm = parse_immediate_value(operands[2], line_num)

    imm_bits    = number_to_binary(imm, 12, line_num)
    funct3      = I_TYPE[opcode]["funct3"]
    opcode_bits = I_TYPE[opcode]["opcode"]

    return imm_bits + rs1 + funct3 + rd + opcode_bits

def encode_s_type(opcode, operands, line_num):
    if len(operands) != 2:
        print(f"Error at line {line_num}: {opcode} needs exactly 2 operands")
        sys.exit(1)
    if operands[0] not in REGISTER_MAP:
        print(f"Error at line {line_num}: Invalid register '{operands[0]}'")
        sys.exit(1)
    rs2_name = operands[0]
    imm_part = operands[1].split("(")[0]
    rs1_name = operands[1].split("(")[1].split(")")[0]
    if rs1_name not in REGISTER_MAP:
        print(f"Error at line {line_num}: Invalid register '{rs1_name}'")
        sys.exit(1)
    rs2 = get_binary_number_of_register_from_register_name(rs2_name, line_num)
    rs1 = get_binary_number_of_register_from_register_name(rs1_name, line_num)
    imm = parse_immediate_value(imm_part, line_num)
    imm_bits    = number_to_binary(imm, 12, line_num)
    imm_front   = imm_bits[0:7]
    imm_back    = imm_bits[7:12]
    opcode_bits = S_TYPE[opcode]["opcode"]
    funct3      = S_TYPE[opcode]["funct3"]
    return imm_front + rs2 + rs1 + funct3 + imm_back + opcode_bits

def encode_b_type(opcode, operands, current_pc, labels, line_num):

    if len(operands) != 3:
        print(f"Error at line {line_num}: {opcode} needs 3 operands")
        sys.exit(1)

    rs1 = get_binary_number_of_register_from_register_name(operands[0], line_num)
    rs2 = get_binary_number_of_register_from_register_name(operands[1], line_num)
    target = operands[2]

    if target[0].isalpha():
        if target not in labels:
            print(f"Error at line {line_num}: Label '{target}' not found")
            sys.exit(1)
        immediate_jahan_jaana_hai = labels[target] - current_pc
    else:
        immediate_jahan_jaana_hai = parse_immediate_value(target, line_num)

    if opcode == "beq":
        funct3 = "000"
    elif opcode == "bne":
        funct3 = "001"
    elif opcode == "blt":
        funct3 = "100"
    elif opcode == "bge":
        funct3 = "101"
    elif opcode == "bltu":
        funct3 = "110"
    elif opcode == "bgeu":
        funct3 = "111"
    else:
        print(f"Error at line {line_num}: Unknown instruction '{opcode}'")
        sys.exit(1)

    imm_bits = number_to_binary(immediate_jahan_jaana_hai, 13, line_num)

    bit12   = imm_bits[0]
    bit11   = imm_bits[1]
    bit10_5 = imm_bits[2:8]
    bit4_1  = imm_bits[8:12]

    final_b_type_ka_khel = bit12 + bit10_5 + rs2 + rs1 + funct3 + bit4_1 + bit11 + "1100011"

    return final_b_type_ka_khel

def encode_u_type(opcode, operands, line_num):
    if len(operands) != 2:
        print(f"Error at line {line_num}: {opcode} needs format: {opcode} rd, imm")
        sys.exit(1)

    rd  = get_binary_number_of_register_from_register_name(operands[0], line_num)
    imm = parse_immediate_value(operands[1], line_num)

    imm_bits = number_to_binary(imm, 20, line_num)

    if opcode == "lui":
        opcode_bits = "0110111"
    elif opcode == "auipc":
        opcode_bits = "0010111"
    else:
        print(f"Error at line {line_num}: Unknown instruction '{opcode}'")
        sys.exit(1)

    return imm_bits + rd + opcode_bits

def encode_j_type(opcode, operands, current_pc, labels, line_num):

    if len(operands) != 2:
        print(f"Error at line {line_num}: jal needs format: jal rd, label")
        sys.exit(1)

    rd     = get_binary_number_of_register_from_register_name(operands[0], line_num)
    target = operands[1]

    if target[0].isalpha():
        if target not in labels:
            print(f"Error at line {line_num}: Label '{target}' not found")
            sys.exit(1)
        imm = labels[target] - current_pc
    else:
        imm = parse_immediate_value(target, line_num)

    imm_bits = number_to_binary(imm, 21, line_num)

    bit20    = imm_bits[0]
    bit19_12 = imm_bits[1:9]
    bit11    = imm_bits[9]
    bit10_1  = imm_bits[10:20]

    return bit20 + bit10_1 + bit11 + bit19_12 + rd + "1101111"
    
def main():
    if len(sys.argv) < 3:
        print("Usage: python3 assembler.py <input.asm> <output.txt>")
        return

    file_input  = sys.argv[1]
    file_output = sys.argv[2]

    try:
        with open(file_input, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: file {file_input} not found.")
        return
    clean_lines = []
    for l in lines:
        if l.strip() != "":
            clean_lines.append(l.strip())
    lines = clean_lines
    if len(lines) == 0:
        print("Error: File is empty.")
        return

    labels = find_all_labels(lines)

    output_lines = []
    instruction_count = 0

    for i in range(len(lines)):
        line = lines[i]
        line_num = i + 1

        if "#" in line:
            line = line[:line.index("#")].strip()

        if line.strip() == "":
            continue

        if ":" in line:
            line = line[line.index(":") + 1:].strip()
            if line == "":
                continue

        opcode, operands = parse_instruction(line)
        if opcode is None:
            continue

        current_pc = instruction_count * 4
        
        if opcode in R_TYPE:
            bits = encode_r_type(opcode, operands, line_num)
        elif opcode in I_TYPE:
            bits = encode_i_type(opcode, operands, line_num)
        elif opcode in S_TYPE:
            bits = encode_s_type(opcode, operands, line_num)
        elif opcode in ("beq", "bne", "blt", "bge", "bltu", "bgeu"):
            bits = encode_b_type(opcode, operands, current_pc, labels, line_num)
        elif opcode in ("lui", "auipc"):
            bits = encode_u_type(opcode, operands, line_num)
        elif opcode == "jal":
            bits = encode_j_type(opcode, operands, current_pc, labels, line_num)
        else:
            print(f"Error at line {line_num}: Unknown instruction '{opcode}'")
            sys.exit(1)

        output_lines.append(bits)
        instruction_count = instruction_count + 1
        
# Text output (for simulator/debugging)
    with open(file_output, "w") as f:
        for bits in output_lines:
            f.write(bits + "\n")

    # Binary output (for kernel/emulator)
    binary_output = file_output + ".raw"

    with open(binary_output, "wb") as f:
        for bits in output_lines:
            value = int(bits, 2)
            f.write(value.to_bytes(4, byteorder="little"))

    print(f"Done! {len(output_lines)} instructions written to {file_output}")
    print(f"Binary image written to {binary_output}")

if __name__ == "__main__":
    main()