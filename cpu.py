"""CPU functionality."""
import pprint
import sys

p_print = pprint.PrettyPrinter(width=30).pprint

# RESERVED REGISTERS
PC = 4
IM = 5
IS = 6
SP = 7
# RESERVED ADDRESSES
STACK_START_ADDRESS = 0b11110011
# OPERATION CODES
HLT = 0b00000001
LDI = 0b10000010
JMP = 0b01010100
PRN = 0b01000111
PUSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
RET = 0b00010001
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110
# ALU OPERATION CODES
ADD = 0b10100000
MUL = 0b10100010
CMP = 0b10100111
AND = 0b10101000
OR = 0b10101010
XOR = 0b10101011
NOT = 0b01101001
SHL = 0b10101100
SHR = 0b10101101
MOD = 0b10100100
# Sprint Challenge


class CPU:
    """Main CPU class."""

    def __init__(self):
        # initialize 256-byte RAM
        self.ram = [0] * 256
        # initialize registers R0 - R7
        self.reg = [0] * 8
        # initialize program counter
        self.reg[PC] = 0
        # set R7, SP (Stack Pointer), to the address of the start of stack
        self.reg[SP] = STACK_START_ADDRESS

        # 00000LGE
        # 00000100 Less Than
        # 00000010 Greater Than
        # 00000001 Equal
        self.fl = 0

        # initializes operation branch table
        self.operations = {
            PRN: self.PRN,
            LDI: self.LDI,
            PUSH: self.PUSH,
            POP: self.POP,
            CALL: self.CALL,
            RET: self.RET,
            JMP: self.JMP,
            JEQ: self.JEQ,
            JNE: self.JNE
        }

    def load(self, program_file_name):
        address = 0
        # reads each line of the program
        with open(program_file_name) as f:
            for line in f:
                # parses each line of binary instruction
                line = line.split('#')
                line = line[0].strip()

                # skips lines that do not contain a binary instruction
                if line == '':
                    continue
                # adds the instruction to RAM at the address value
                # and increments the address
                self.ram[address] = int(line, 2)
                address += 1

    def alu(self, op, operand_a, operand_b=None):
        reg_a = operand_a
        reg_b = operand_b

        def _CMP():
            if self.reg[reg_a] < self.reg[reg_b]:
                return 0b00000100
            elif self.reg[reg_a] > self.reg[reg_b]:
                return 0b00000010
            elif self.reg[reg_a] == self.reg[reg_b]:
                return 0b00000001

        # branchtable for ALU operations
        alu_operations = {
            ADD: self.reg[reg_a] + self.reg[reg_b],
            MUL: self.reg[reg_a] * self.reg[reg_b],
            CMP: _CMP,
            AND: self.reg[reg_a] & self.reg[reg_b],
            OR: self.reg[reg_a] | self.reg[reg_b],
            XOR: self.reg[reg_a] ^ self.reg[reg_b],
            NOT: ~(self.reg[reg_a]),
            #    bit-wise shifts left, and fills the low bits with 0
            SHL: (self.reg[reg_a] << self.reg[reg_b]) & 0b11111111,
            #    bit-wise shifts right, high bits are implicitly filled with 0's
            SHR: (self.reg[reg_a] >> self.reg[reg_b]),
            MOD: self.reg[reg_a] % self.reg[reg_b]
        }

        if op is CMP:
            self.fl = _CMP()
        elif op in alu_operations:
            self.reg[reg_a] = alu_operations[op]

        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.reg[PC],
            # self.fl,
            # self.ie,
            self.ram_read(self.reg[PC]),
            self.ram_read(self.reg[PC] + 1),
            self.ram_read(self.reg[PC] + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def ram_read(self, mar):
        # returns the MDR (Memory Data Register)
        return self.ram[mar]

    def ram_write(self, mar, mdr):
        # writes the MDR (Memory Data Register)
        # to the MAR (Memory Address Register)
        self.ram[mar] = mdr

    def run(self):
        running = True
        while running:
            next_instruction = self.ram_read(self.reg[PC])
            running = self.execute(next_instruction)

    def execute(self, instruction):
        # parses instruction and stores in 'inst' as dict
        inst = self.parse_instruction(instruction)
        # returns false to terminate run-loop
        if instruction is HLT:
            return False

        # destructures parsed 'inst' dict
        num_ops, is_alu, sets_pc, inst_id = inst.values()

        # reads the operands from memory and stores it in each operand
        operand_a = self.ram_read(self.reg[PC] + 1)
        operand_b = self.ram_read(self.reg[PC] + 2)
        # redirects to ALU if instruction is an ALU instruction
        if is_alu:
            self.alu(instruction, operand_a, operand_b)

        # otherwise executes directly from the `operations` branch-table
        else:
            self.operations[instruction](operand_a, operand_b)

        if not sets_pc:
            self.reg[PC] += num_ops + 1

        # returns true to continue run-loop
        return True

    def parse_instruction(self, inst):
        # number of operands
        # masks all but first 2 bits, bit-wise shifts 6 to right, castes to int
        num_ops = int((0b11000000 & inst) >> 6)
        # whether the instruction should be passed to the ALU
        # masks all but 3rd bit, bit-wise shifts 5 to right, castes to bool
        is_alu = bool((0b00100000 & inst) >> 5)
        # whether the instruction sets the pc
        # masks all but 4th bit, bit-wise shifts 4 to right, castes to bool
        sets_pc = bool((0b00010000 & inst) >> 4)
        # the actual identifier of the instruction (masking all the bits above)
        # masks all but last four bits
        inst_id = 0b00001111 & inst

        # returns vals as a dictionary
        return {
            "num_ops": num_ops,
            "is_alu": is_alu,
            "sets_pc": sets_pc,
            "inst_id": inst_id
        }

    def JMP(self, operand_a, operand_b=None):
        target_reg = operand_a

        # calls the instruction stored in the target register
        self.CALL(target_reg, None)

        # sets the PC equal to the instruction address
        inst_address = self.reg[target_reg]
        self.reg[PC] = inst_address

    def JEQ(self, operand_a, operand_b):
        target_reg = operand_a

        # masks all but the equal bit and castes to bool
        is_equal = bool((0b00000001) & self.fl)

        # jumps to target instruction if the equals flag is true
        if is_equal:
            self.JMP(target_reg)
        # otherwise increments the PC to the next instruction
        else:
            self.reg[PC] += 2

    def JNE(self, operand_a, operand_b=None):
        target_reg = operand_a

        # masks all but the equal bit and castes to bool
        is_equal = bool((0b00000001) & self.fl)

        # jumps to target instruction if the equals flag is false
        if not is_equal:
            self.JMP(target_reg)
        # otherwise increments the PC to the next instruction
        else:
            self.reg[PC] += 2

    def PRN(self, operand_a, operand_b=None):
        # extracts the target register from the operand
        target_reg = operand_a
        # extracts the value stored in the target register
        value = self.reg[target_reg]
        print(value)

    def LDI(self, operand_a, operand_b):
        # extracts the target register and value from the operands
        target_reg = operand_a
        value = operand_b
        # set the value to the target register
        self.reg[target_reg] = value

    def PUSH(self, operand_a, operand_b=None):
        # extract the target register from the operand
        target_reg = operand_a
        # decrements the SP
        self.reg[SP] -= 1
        # extracts the value stored in the target register
        value = self.reg[target_reg]
        # extracts the stack address stored in the SP register
        stack_address = self.reg[SP]
        # writes the value to the stack address in RAM
        self.ram_write(stack_address, value)

    def POP(self, operand_a, operand_b=None):
        # extracts the target register from the operand
        target_reg = operand_a
        # extracts the stack address stored in the SP register
        stack_address = self.reg[SP]
        # extracts the value read from RAM at the stack address
        value = self.ram_read(stack_address)
        # stores the value in the target register
        self.reg[target_reg] = value
        # increments the SP
        self.reg[SP] += 1

    def CALL(self, operand_a, operand_b=None):
        # extract the target register from the operand
        target_reg = operand_a
        # increments the PC to the next instruction
        self.reg[PC] += 2
        # pushes the next instruction at the PC onto the stack
        self.PUSH(PC)
        # extracts the address of the sub routine from the target register
        sub_routine_address = self.reg[target_reg]
        # sets the PC to the sub routine address
        self.reg[PC] = sub_routine_address

    def RET(self, operand_a, operand_b=None):
        # pops the return address from the stack
        # and stores it in the PC
        self.POP(PC)
