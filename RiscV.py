class RiscV:
    
    pc = 0x10074;
    rf = [0 for k in range(32)];
    dmem = [0 for k in range(1024)];

    def __init__ (self, dump):

        # Parse the dump file
        with open(dump) as f:
            file_content = f.read().splitlines();
        
        ref_dict = list();
        dict_aux = {'addr': '', 'hex': '', 'mn': '', 'args': list()};
        for line in file_content[6:]:
            if (line.find("<") == -1):
                aux = line.split();
                dict_aux['addr'] = aux[0].strip()[0:-1];
                dict_aux['hex'] = aux[1].strip();
                dict_aux['mn'] = aux[2].strip();
                if (len(aux) > 3):
                    dict_aux['args'] = aux[3].strip();
        
                ref_dict.append(dict_aux.copy());
                dict_aux['args'] = list();
            else:
                if (line.find('main')):
                    aux = line.split();
                    self.pc = int('0x' + aux[0], 16);

        # Build the instruction memory address and data
        self.instr_mem = [{'addr': '', 'instr': ''} for k in range(len(ref_dict))];
        for i in range(len(ref_dict)):
            self.instr_mem[i]['addr'] = ref_dict[i]['addr'];
            self.instr_mem[i]['instr'] = ref_dict[i]['hex'];

        addr_list = [int('0x' + i['addr'],16) for i in self.instr_mem]; 
        self.min_addr = min(addr_list);

        # Create reference for decoder
        self.instr_mnemonic_ref = [ref_dict[k]['mn'] for k in range(len(self.instr_mem))];
        
        args_tmp = [ref_dict[k]['args'] for k in range(len(self.instr_mem))];
        self.instr_args_ref = self.set_args(self.instr_mnemonic_ref, args_tmp) ;

        for i in range(len(self.instr_mem)):
            print(self.instr_mnemonic_ref[i]);
            self.decode_instr(self.instr_mem[i]['instr']);
            print(self.rf);
            print(self.dmem[480:501]);
            print();
            

    # Decode instruction
    def decode_instr (self, instr):
        # Convert o bin, fill the 32 required bits and reverse the strig (LSB on zero)
        instr_bin = bin(int(instr,16))[2:].zfill(32)[::-1];

        # Distiguish instruction fields
        rd = int(instr_bin[7:12][::-1], 2);
        rs1 = int(instr_bin[15:20][::-1], 2);
        rs2 = int(instr_bin[20:25][::-1], 2);
        immi = int(instr_bin[20:][::-1], 2);
        imms = int((instr_bin[7:12]+instr_bin[25:])[::-1], 2);
        immb = int(('0'+instr_bin[8:12]+instr_bin[25:31]+instr_bin[7]+instr_bin[31])[::-1], 2);
        immj = int(('0'+instr_bin[21:31]+instr_bin[20]+instr_bin[12:20]+instr_bin[31])[::-1], 2);
        immu = int((instr_bin[12:])[::-1], 2);

        change_pc = False;
        
        # ISA: RV32I
        if (instr_bin[0:7] == '1100110'):
            print("This is a R-Type");
            if (instr_bin[12:15] == '000'):
                # ADD
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] + self.rf[rs2]);
                # SUB
                if (instr_bin[25:] == '0000010'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] - self.rf[rs2]);
                # MUL
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_mul = sig_rs1 * sig_rs2;
                    self.rf[rd] = sig_mul & 0x00000000ffffffff;
            if (instr_bin[12:15] == '100'):
                # SLL
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] << (self.rf[rs2]&0x1f));
                # MULH
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_mul = sig_rs1 * sig_rs2;
                    usig_mul_32 = (sig_mul & 0xffffffffffffffff) >> 32;
                    self.rf[rd] = self.sign_extend(usig_mul_32,32);
            if (instr_bin[12:15] == '010'):
                # SLT
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = 1 if (self.rf[rs1] < self.rf[rs2]) else 0;
                # MULHSU
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    sig_mul = sig_rs1 * usig_rs2;
                    usig_mul_32 = (sig_mul & 0xffffffffffffffff) >> 32;
                    self.rf[rd] = self.sign_extend(usig_mul_32,32);
            if (instr_bin[12:15] == '110'):
                # SLTU
                if (instr_bin[25:] == '0000000'):
                    if (self.rf[rs1] < 0):
                        rs1_u = self.rf[rs1]+2**32;
                    else:
                        rs1_u = self.rf[rs1];
                    if (self.rf[rs2] < 0):
                        rs2_u = self.rf[rs2]+2**32;
                    else:
                        rs2_u = self.rf[rs2];
                    self.rf[rd] = 1 if (rs1_u < rs2_u) else 0;
                # MULHU
                if (instr_bin[25:] == '1000000'):
                    usig_rs1 = self.usig_word(self.rf[rs1]);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    usig_mul = usig_rs1 * usig_rs2;
                    usig_mul_32 = (usig_mul & 0xffffffffffffffff) >> 32;
                    self.rf[rd] = self.sign_extend(usig_mul_32,32);
            if (instr_bin[12:15] == '001'):
                # XOR
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.rf[rs1] ^ self.rf[rs2];
                # DIV
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_div_trunc = int(sig_rs1/sig_rs2);
                    self.rf[rd] = self.sign_extend(sig_div_trunc,32);
            if (instr_bin[12:15] == '101'):
                # SRL
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.trim_word((self.rf[rs1] & 0xffffffff) >> (self.rf[rs2]&0x1f));
                # SRA
                if (instr_bin[25:] == '0000010'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] >> (self.rf[rs2]%0x1f));
                # DIVU
                if (instr_bin[25:] == '1000000'):
                    usig_rs1 = self.usig_word(self.rf[rs1]);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    usig_div_trunc = int(usig_rs1/usig_rs2);
                    self.rf[rd] = self.sign_extend(usig_div_trunc,32);
            if (instr_bin[12:15] == '011'):
                # OR
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.rf[rs1] | self.rf[rs2];
                # REM
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_rem_trunc = int(sig_rs1%sig_rs2);
                    self.rf[rd] = self.sign_extend(sig_rem_trunc,32);
            if (instr_bin[12:15] == '111'):
                # AND
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.rf[rs1] & self.rf[rs2];
                # REMU
                if (instr_bin[25:] == '1000000'):
                    usig_rs1 = self.usig_word(self.rf[rs1]);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    usig_rem_trunc = int(usig_rs1%usig_rs2);
                    self.rf[rd] = self.sign_extend(usig_rem_trunc,32);

        elif (instr_bin[0:7] == '1100100'):
            print("This is a I-Type");
            # ADDI
            if (instr_bin[12:15] == '000'):
                self.rf[rd] = self.trim_word(self.rf[rs1] + self.sign_extend(immi, 12));
            # SLTI
            if (instr_bin[12:15] == '010'):
                self.rf[rd] = 1 if self.rf[rs1] < self.sign_extend(immi, 12) else 0;
            # SLTIU
            if (instr_bin[12:15] == '110'):
                self.rf[rd] = 1 if abs(self.rf[rs1]) < immi else 0;
            # XORI 
            if (instr_bin[12:15] == '001'):
                self.rf[rd] = self.rf[rs1] ^ self.sign_extend(immi,12);
            # ORI 
            if (instr_bin[12:15] == '011'):
                self.rf[rd] = self.rf[rs1] | self.sign_extend(immi,12);
            # ANDI 
            if (instr_bin[12:15] == '111'):
                self.rf[rd] = self.rf[rs1] & self.sign_extend(immi,12);
            # SLLI
            if (instr_bin[12:15] == '100' and instr_bin[25:] == '0000000'):
                self.rf[rd] = self.trim_word((self.rf[rs1] & 0xffffffff) << rs2);
            # SRLI
            if (instr_bin[12:15] == '101' and instr_bin[25:] == '0000000'):
                self.rf[rd] = self.trim_word((self.rf[rs1] & 0xffffffff) >> rs2);
            # SRAI
            if (instr_bin[12:15] == '101' and instr_bin[25:] == '0000010'):
                self.rf[rd] = self.trim_word(self.rf[rs1] >> rs2);

        elif (instr_bin[0:7] == '1100010'):
            print("This is a S-Type");
            # SW
            if (instr_bin[12:15] == '010'): 
                addr = self.rf[rs1]+self.sign_extend(imms,12);
                self.mem_func(0, addr, self.rf[rs2]);
            # SH
            if (instr_bin[12:15] == '100'): 
                addr = self.rf[rs1]+self.sign_extend(imms,12);
                data = (self.rf[rs2] & 0x0000ffff) + (dmem[addr] & 0xffff0000);
                self.mem_func(0, addr, data);
            # SB
            if (instr_bin[12:15] == '100'): 
                addr = self.rf[rs1]+self.sign_extend(imms,12);
                data = (self.rf[rs2] & 0x000000ff) + (dmem[addr] & 0xffffff00);
                self.mem_func(0, addr, data);

        elif (instr_bin[0:7] == '1100000'):
            print("This is a I-Type, but load");
            # LB
            if (instr_bin[12:15] == '000'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                read_data = self.sign_extend(self.mem_func(1, addr, 0) & 0x000000ff, 8);
                self.rf[rd] = read_data;
            # LH
            if (instr_bin[12:15] == '100'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                read_data = self.sign_extend(self.mem_func(1, addr, 0) & 0x0000ffff, 16);
                self.rf[rd] = read_data;
            # LW
            if (instr_bin[12:15] == '010'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                read_data = self.mem_func(1, addr, 0);
                self.rf[rd] = read_data;
            # LBU
            if (instr_bin[12:15] == '001'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                read_data = self.mem_func(1, addr, 0) & 0x000000ff;
                self.rf[rd] = read_data;
            # LHU
            if (instr_bin[12:15] == '101'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                read_data = self.mem_func(1, addr, 0) & 0x0000ffff;
                self.rf[rd] = read_data;

        elif (instr_bin[0:7] == '1100011'):
            print("This is a SB-Type");
            # BEQ
            if (instr_bin[12:15] == '000'): 
                if (self.rf[rs1] == self.rf[rs2]):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
            # BNE
            if (instr_bin[12:15] == '100'): 
                if (self.rf[rs1] != self.rf[rs2]):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
            # BLT
            if (instr_bin[12:15] == '001'): 
                sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                if (sig_rs1 < sig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
            # BGE
            if (instr_bin[12:15] == '101'): 
                sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                if (sig_rs1 >= sig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
            # BLTU
            if (instr_bin[12:15] == '011'): 
                usig_rs1 = self.usig_word(self.rf[rs1]);
                usig_rs2 = self.usig_word(self.rf[rs2]);
                if (usig_rs1 < usig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
            # BGEU
            if (instr_bin[12:15] == '111'): 
                usig_rs1 = self.usig_word(self.rf[rs1]);
                usig_rs2 = self.usig_word(self.rf[rs2]);
                if (usig_rs1 >= usig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;

        elif (instr_bin[0:7] == '1110011'):
            print("This is a I-Type, but jump");
            # JALR 
            if (instr_bin[12:15] == '000'): 
                self.rf[rd] = self.pc + 4;
                usig_rs1 = self.usig_word(self.rf[rs1]);
                self.pc = self.usig_word(usig_rs1 + self.sign_extend(immi,12));
                change_pc = True;

        # JAL 
        elif (instr_bin[0:7] == '1111011'):
            print("This is a J-Type");
            self.rf[rd] = self.pc + 4;
            self.pc = self.pc + self.sign_extend(immj,21);
            change_pc = True;
        
        # AUIPC 
        elif (instr_bin[0:7] == '1110100'):
            print("This is a U-Type");
            self.rf[rd] = self.pc + self.sign_extend(immu << 12);

        # LUI 
        elif (instr_bin[0:7] == '1110110'):
            print("This is a U-Type");
            self.rf[rd] = self.sign_extend(immu << 12);

        if (not(change_pc)):
            self.pc = self.pc + 4;

        print(f'RD: {self.rf[rd]}')
        print(f'R1: {self.rf[rs1]}')
        print(f'R2: {self.rf[rs2]}')


    def mem_func (self, rwn, addr, d_in):
        if (not(rwn)):
            addr_word = int(addr/4);
            self.dmem[addr_word] = d_in;
            return True;
        else:
            addr_word = int(addr/4);
            return self.dmem[addr_word];


    # TODO: Evaluate change the trim_word(,32) to sign_extend(,32);
    def trim_word (self, number, sbit = 32):
        if (abs(number) > 2**(sbit-1)-1):
            return number & 0x00000000ffffffff;
        else:
            return number;

    def sign_extend(self, value, bits):
        sign_bit = 1 << (bits - 1)
        return (value & (sign_bit - 1)) - (value & sign_bit)

    def usig_word(self, value):
        if (value < 0):
            return value + 2**32;
        else:
            return value;


    # Setup reference arguments based on dump file
    def set_args (self, mnemonic_list, instr_args):
        instr_args_list = list();
        for mn, iargs in zip(mnemonic_list, instr_args):
            if (mn == 'and' or mn == 'or' or mn == 'sra' or mn == 'srl' or \
                mn == 'xor' or mn == 'sltu' or mn == 'slt' or mn == 'sll' or \
                mn == 'sub' or mn == 'add' or mn == 'mul' or mn == 'mulh' or \
                mn == 'mulhsu' or mn == 'mulhu' or mn == 'div' or mn == 'divu' or \
                mn == 'rem' or mn == 'remu'):
                
                aux = iargs.split(',');
                instr_args_list.append({'rd': aux[0], 'rs1': aux[1], 'rs2': aux[2]});

            elif (mn == 'lui' or mn == 'auipc'):

                aux = iargs.split(',');
                instr_args_list.append({'rd': aux[0], 'imm': aux[1]});

            elif (mn == 'beq' or mn == 'bne' or mn == 'blt' or mn == 'bge' or \
                  mn == 'bltu' or mn == 'bgeu'):
            
                aux = iargs.split(',');
                instr_args_list.append({'rs1': aux[0], 'rs2': aux[1], 'imm': aux[2]});

            elif (mn == 'jal'):

                aux = iargs.split(',');
                instr_args_list.append({'rd': aux[0], 'imm': aux[1]});

            elif (mn == 'jalr'):

                aux = iargs.split(',');
                instr_args_list.append({'rd': aux[0], 'rs1': aux[1], 'imm': aux[2]});

            elif (mn == 'lb' or mn == 'lh' or mn == 'lw' or \
                  mn == 'lbu' or mn == 'lhu'):

                aux = iargs.split(',');
                aux1 = aux[-1].split('(');
                aux = [aux[0], aux1[1][0:-1], aux1[0]];
                instr_args_list.append({'rd': aux[0], 'rs1': aux[1], 'imm': aux[2]});

            elif (mn == 'addi' or mn == 'slti' or \
                  mn == 'sltiu' or mn == 'xori' or mn == 'ori' or mn == 'andi'):

                aux = iargs.split(',');
                instr_args_list.append({'rd': iargs[0], 'rs1': iargs[1], 'imm': iargs[2]});

            elif (mn == 'sb' or mn == 'sh' or mn == 'sw'):

                aux = iargs.split(',');
                aux1 = aux[-1].split('(');
                aux = [aux[0], aux1[1][0:-1], aux1[0]];
                instr_args_list.append({'rd': aux[0], 'rs1': aux[1], 'imm': aux[2]});

            elif (mn == 'slli' or mn == 'srli' or mn == 'srai'):

                aux = iargs.split(',');
                instr_args_list.append({'rd': aux[0], 'rs1': aux[1], 'imm': aux[2]});

        return instr_args_list;
