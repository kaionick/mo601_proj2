class RiscV:
    
    pc = 0x0;
    rf = [0 for k in range(32)];
    dmem = [0 for k in range(0xffffff)];
    instr_mem = [0 for k in range(0xFFFFFF)];
    log = '';

    # Reference ABI list
    abi_list = ['zero','ra','sp','gp','tp','t0','t1','t2','s0','s1','a0','a1',
                'a2','a3','a4','a5','a6','a7','s2','s3','s4','s5','s6','s7',
                's8','s9','s10','s11','t3','t4','t5','t6'];

    def __init__ (self, dump):

        # Define log name
        self.log_name = self.get_log_name(dump);

        # Parse the dump file
        with open(dump) as f:
            file_content = f.read().splitlines();
        
        ref_dict = list();
        dict_aux = {'addr': '', 'hex': '', 'mn': '', 'args': list()};
        for line in file_content[6:]:
            if (line.find(">:") == -1 and line != ''):
                aux = line.split();
                #print(aux);
                dict_aux['addr'] = aux[0].strip()[0:-1];
                dict_aux['hex'] = aux[1].strip();
                dict_aux['mn'] = aux[2].strip();
                if (len(aux) > 3):
                    dict_aux['args'] = aux[3].strip();
        
                ref_dict.append(dict_aux.copy());
                dict_aux['args'] = list();
            else:
                if (line.find('<_start>') > 0):
                    #print(line);
                    aux = line.split();
                    self.pc = int('0x' + aux[0], 16);

        #print(f'Start address: {self.pc}');
        # Build the instruction memory address and data
        for i in range(len(ref_dict)):
            addr_idx = int(int('0x' + ref_dict[i]['addr'],16)/4);
            self.instr_mem[addr_idx] = ref_dict[i]['hex'];

        # Create reference for decoder
        self.instr_mnemonic_ref = [ref_dict[k]['mn'] for k in range(len(ref_dict))];
        
        #args_tmp = [ref_dict[k]['args'] for k in range(len(ref_dict))];
        #self.instr_args_ref = self.set_args(self.instr_mnemonic_ref, args_tmp) ;

        # Set initial RA to end the program
        self.rf[1] = 0xffffffff;
        # Set initial SP to guide memory write/read
        self.rf[2] = 500;

        eop = False;
        while(not(eop)):
            #print(f'PC: {self.pc}');
            #print(self.instr_mnemonic_ref[int(self.pc/4)]);
            eop = self.decode_instr(self.instr_mem[int(self.pc/4)]);
            #if (dump == '/home/kaio/Documents/MO601/proj2/riscv_simu/test/121.loop.riscv.dump'):
            #    print(f'PC: {self.pc}');
            #print(self.rf);
            #print(self.dmem[480:501]);
            #print();


    # Decode instruction
    def decode_instr (self, instr):
        # Convert o bin, fill the 32 required bits and reverse the strig (LSB on zero)
        #print(f'Instr: {instr}');
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

        # Flag to indicate PC change from instruction or not
        change_pc = False;

        # Flag to signal end of program
        eop = False;

        # Log variables
        pc_cur = self.pc;
        dasm_str = '';

        rs1_old = self.rf[rs1];
        rs2_old = self.rf[rs2];
        
        #print(f'ZERO: {self.rf[0]}');
        # ISA: RV32I
        if (instr_bin[0:7] == '1100110'):
            #print("This is a R-Type");
            if (instr_bin[12:15] == '000'):
                # ADD
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] + self.rf[rs2]);
                    dasm_str = self.build_dasm('add', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # SUB
                if (instr_bin[25:] == '0000010'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] - self.rf[rs2]);
                    dasm_str = self.build_dasm('sub', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # MUL
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_mul = sig_rs1 * sig_rs2;
                    self.rf[rd] = sig_mul & 0x00000000ffffffff;
                    dasm_str = self.build_dasm('mul', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
            if (instr_bin[12:15] == '100'):
                # SLL
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] << (self.rf[rs2]&0x1f));
                    dasm_str = self.build_dasm('sll', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # MULH
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_mul = sig_rs1 * sig_rs2;
                    usig_mul_32 = (sig_mul & 0xffffffffffffffff) >> 32;
                    self.rf[rd] = self.sign_extend(usig_mul_32,32);
                    dasm_str = self.build_dasm('mulh', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
            if (instr_bin[12:15] == '010'):
                # SLT
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = 1 if (self.rf[rs1] < self.rf[rs2]) else 0;
                    dasm_str = self.build_dasm('slt', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # MULHSU
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    sig_mul = sig_rs1 * usig_rs2;
                    usig_mul_32 = (sig_mul & 0xffffffffffffffff) >> 32;
                    self.rf[rd] = self.sign_extend(usig_mul_32,32);
                    dasm_str = self.build_dasm('mulhsu', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
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
                    dasm_str = self.build_dasm('sltu', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # MULHU
                if (instr_bin[25:] == '1000000'):
                    usig_rs1 = self.usig_word(self.rf[rs1]);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    usig_mul = usig_rs1 * usig_rs2;
                    usig_mul_32 = (usig_mul & 0xffffffffffffffff) >> 32;
                    self.rf[rd] = self.sign_extend(usig_mul_32,32);
                    dasm_str = self.build_dasm('mulhu', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
            if (instr_bin[12:15] == '001'):
                # XOR
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.rf[rs1] ^ self.rf[rs2];
                    dasm_str = self.build_dasm('xor', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # DIV
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_div_trunc = int(sig_rs1/sig_rs2);
                    self.rf[rd] = self.sign_extend(sig_div_trunc,32);
                    dasm_str = self.build_dasm('div', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
            if (instr_bin[12:15] == '101'):
                # SRL
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.trim_word((self.rf[rs1] & 0xffffffff) >> (self.rf[rs2]&0x1f));
                    dasm_str = self.build_dasm('srl', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # SRA
                if (instr_bin[25:] == '0000010'):
                    self.rf[rd] = self.trim_word(self.rf[rs1] >> (self.rf[rs2]%0x1f));
                    dasm_str = self.build_dasm('sra', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # DIVU
                if (instr_bin[25:] == '1000000'):
                    usig_rs1 = self.usig_word(self.rf[rs1]);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    usig_div_trunc = int(usig_rs1/usig_rs2);
                    self.rf[rd] = self.sign_extend(usig_div_trunc,32);
                    dasm_str = self.build_dasm('divu', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
            if (instr_bin[12:15] == '011'):
                # OR
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.rf[rs1] | self.rf[rs2];
                    dasm_str = self.build_dasm('or', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # REM
                if (instr_bin[25:] == '1000000'):
                    sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                    sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                    sig_rem_trunc = int(sig_rs1%sig_rs2);
                    self.rf[rd] = self.sign_extend(sig_rem_trunc,32);
                    dasm_str = self.build_dasm('rem', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
            if (instr_bin[12:15] == '111'):
                # AND
                if (instr_bin[25:] == '0000000'):
                    self.rf[rd] = self.rf[rs1] & self.rf[rs2];
                    dasm_str = self.build_dasm('and', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);
                # REMU
                if (instr_bin[25:] == '1000000'):
                    usig_rs1 = self.usig_word(self.rf[rs1]);
                    usig_rs2 = self.usig_word(self.rf[rs2]);
                    usig_rem_trunc = int(usig_rs1%usig_rs2);
                    self.rf[rd] = self.sign_extend(usig_rem_trunc,32);
                    dasm_str = self.build_dasm('remu', rd, rs1, rs2, 
                                               immi, imms, immb, immj, immu);

        elif (instr_bin[0:7] == '1100100'):
            #print("This is a I-Type");
            # ADDI
            if (instr_bin[12:15] == '000'):
                self.rf[rd] = self.trim_word(self.rf[rs1] + self.sign_extend(immi, 12));
                dasm_str = self.build_dasm('addi', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # SLTI
            if (instr_bin[12:15] == '010'):
                self.rf[rd] = 1 if self.rf[rs1] < self.sign_extend(immi, 12) else 0;
                dasm_str = self.build_dasm('slti', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # SLTIU
            if (instr_bin[12:15] == '110'):
                self.rf[rd] = 1 if abs(self.rf[rs1]) < immi else 0;
                dasm_str = self.build_dasm('sltiu', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # XORI 
            if (instr_bin[12:15] == '001'):
                self.rf[rd] = self.rf[rs1] ^ self.sign_extend(immi,12);
                dasm_str = self.build_dasm('xori', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # ORI 
            if (instr_bin[12:15] == '011'):
                self.rf[rd] = self.rf[rs1] | self.sign_extend(immi,12);
                dasm_str = self.build_dasm('ori', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # ANDI 
            if (instr_bin[12:15] == '111'):
                self.rf[rd] = self.rf[rs1] & self.sign_extend(immi,12);
                dasm_str = self.build_dasm('andi', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # SLLI
            if (instr_bin[12:15] == '100' and instr_bin[25:] == '0000000'):
                self.rf[rd] = self.trim_word((self.rf[rs1] & 0xffffffff) << rs2);
                dasm_str = self.build_dasm('slli', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # SRLI
            if (instr_bin[12:15] == '101' and instr_bin[25:] == '0000000'):
                self.rf[rd] = self.trim_word((self.rf[rs1] & 0xffffffff) >> rs2);
                dasm_str = self.build_dasm('srli', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # SRAI
            if (instr_bin[12:15] == '101' and instr_bin[25:] == '0000010'):
                self.rf[rd] = self.trim_word(self.rf[rs1] >> rs2);
                dasm_str = self.build_dasm('srai', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);

        elif (instr_bin[0:7] == '1100010'):
            #print("This is a S-Type");
            # SW
            if (instr_bin[12:15] == '010'): 
                addr = self.rf[rs1]+self.sign_extend(imms,12);
                self.mem_func(0, addr, self.rf[rs2]);
                dasm_str = self.build_dasm('sw', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # SH
            if (instr_bin[12:15] == '100'): 
                addr = self.rf[rs1]+self.sign_extend(imms,12);
                addr_r = addr % 4;
                if (addr_r == 0):
                    data = (self.rf[rs2] & 0x0000ffff) + (self.dmem[int(addr/4)] & 0xffff0000);
                else:
                    data = ((self.rf[rs2] & 0x0000ffff) << 16) + (self.dmem[int(addr/4)] & 0x0000ffff);
                self.mem_func(0, addr, data);
                dasm_str = self.build_dasm('sh', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # SB
            if (instr_bin[12:15] == '000'): 
                addr = self.rf[rs1]+self.sign_extend(imms,12);
                addr_r = addr % 4;
                if (addr_r == 0):
                    data = (self.rf[rs2] & 0x000000ff) + (self.dmem[int(addr/4)] & 0xffffff00);
                elif (addr_r == 1):
                    data = ((self.rf[rs2] & 0x000000ff) << 8) + (self.dmem[int(addr/4)] & 0xffff00ff);
                elif (addr_r == 2):
                    data = ((self.rf[rs2] & 0x000000ff) << 16) + (self.dmem[int(addr/4)] & 0xff00ffff);
                elif (addr_r == 3):
                    data = ((self.rf[rs2] & 0x000000ff) << 24) + (self.dmem[int(addr/4)] & 0x00ffffff);
                #print(f'ADDR: {addr}');
                #print(f'ADDR_R: {addr_r}');
                #print(hex(data));
                self.mem_func(0, addr, data);
                dasm_str = self.build_dasm('sb', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);

        elif (instr_bin[0:7] == '1100000'):
            #print("This is a I-Type, but load");
            # LB
            if (instr_bin[12:15] == '000'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                addr_r = addr % 4;
                read_data = self.mem_func(1, addr, 0);
                if (addr_r == 0):
                    self.rf[rd] = self.sign_extend((read_data & 0x000000ff), 8);
                elif (addr_r == 1):
                    self.rf[rd] = self.sign_extend(((read_data & 0x0000ff00)>>8), 8);
                elif (addr_r == 2):
                    self.rf[rd] = self.sign_extend(((read_data & 0x00ff0000)>>16), 8);
                elif (addr_r == 3):
                    self.rf[rd] = self.sign_extend(((read_data & 0xff000000)>>24), 8);
                dasm_str = self.build_dasm('lb', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # LH
            if (instr_bin[12:15] == '100'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                addr_r = addr % 4;
                read_data = self.mem_func(1, addr, 0);
                if (addr_r == 0):
                    self.rf[rd] = self.sign_extend((read_data & 0x0000ffff), 16);
                else:
                    self.rf[rd] = self.sign_extend(((read_data & 0xffff0000)>>16), 16);
                dasm_str = self.build_dasm('lh', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # LW
            if (instr_bin[12:15] == '010'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                read_data = self.mem_func(1, addr, 0);
                self.rf[rd] = read_data;
                dasm_str = self.build_dasm('lw', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # LBU
            if (instr_bin[12:15] == '001'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                addr_r = addr % 4;
                read_data = self.mem_func(1, addr, 0);
                if (addr_r == 0):
                    self.rf[rd] = (read_data & 0x000000ff);
                elif (addr_r == 1):
                    self.rf[rd] = ((read_data & 0x0000ff00)>>8);
                elif (addr_r == 2):
                    self.rf[rd] = ((read_data & 0x00ff0000)>>16);
                elif (addr_r == 3):
                    self.rf[rd] = ((read_data & 0xff000000)>>24);
                dasm_str = self.build_dasm('lbu', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # LHU
            if (instr_bin[12:15] == '101'): 
                addr = self.rf[rs1]+self.sign_extend(immi,12);
                addr_r = addr % 4;
                read_data = self.mem_func(1, addr, 0);
                if (addr_r == 0):
                    self.rf[rd] = (read_data & 0x0000ffff);
                else:
                    self.rf[rd] = ((read_data & 0xffff0000)>>16);
                dasm_str = self.build_dasm('lhu', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);

        elif (instr_bin[0:7] == '1100011'):
            #print("This is a SB-Type");
            # BEQ
            if (instr_bin[12:15] == '000'): 
                if (self.rf[rs1] == self.rf[rs2]):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
                dasm_str = self.build_dasm('beq', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # BNE
            if (instr_bin[12:15] == '100'): 
                #print(f'RS1[{rs1}]: {self.rf[rs1]}')
                #print(f'RS2[{rs2}]: {self.rf[rs2]}')
                if (self.rf[rs1] != self.rf[rs2]):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
                dasm_str = self.build_dasm('bne', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # BLT
            if (instr_bin[12:15] == '001'): 
                sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                if (sig_rs1 < sig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
                dasm_str = self.build_dasm('blt', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # BGE
            if (instr_bin[12:15] == '101'): 
                sig_rs1 = self.sign_extend(self.rf[rs1], 32);
                sig_rs2 = self.sign_extend(self.rf[rs2], 32);
                if (sig_rs1 >= sig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
                dasm_str = self.build_dasm('bge', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # BLTU
            if (instr_bin[12:15] == '011'): 
                usig_rs1 = self.usig_word(self.rf[rs1]);
                usig_rs2 = self.usig_word(self.rf[rs2]);
                if (usig_rs1 < usig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
                dasm_str = self.build_dasm('bltu', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # BGEU
            if (instr_bin[12:15] == '111'): 
                usig_rs1 = self.usig_word(self.rf[rs1]);
                usig_rs2 = self.usig_word(self.rf[rs2]);
                if (usig_rs1 >= usig_rs2):
                    self.pc = self.pc + self.sign_extend(immb,13);
                    change_pc = True;
                dasm_str = self.build_dasm('bgeu', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);

        elif (instr_bin[0:7] == '1110011'):
            #print("This is a I-Type, but jump");
            # JALR 
            if (instr_bin[12:15] == '000'): 
                self.rf[rd] = self.pc + 4;
                usig_rs1 = self.usig_word(self.rf[rs1]);
                self.pc = self.usig_word(usig_rs1 + self.sign_extend(immi,12));
                change_pc = True;
                dasm_str = self.build_dasm('jalr', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);

        # JAL 
        elif (instr_bin[0:7] == '1111011'):
            #print("This is a J-Type");
            self.rf[rd] = self.pc + 4;
            self.pc = self.pc + self.sign_extend(immj,21);
            change_pc = True;
            dasm_str = self.build_dasm('jal', rd, rs1, rs2, 
                                       immi, imms, immb, immj, immu);
        
        # AUIPC 
        elif (instr_bin[0:7] == '1110100'):
            #print("This is a U-Type");
            self.rf[rd] = self.pc + self.sign_extend(immu << 12,32);
            dasm_str = self.build_dasm('auipc', rd, rs1, rs2, 
                                       immi, imms, immb, immj, immu);

        # LUI 
        elif (instr_bin[0:7] == '1110110'):
            #print("This is a U-Type");
            self.rf[rd] = self.sign_extend(immu << 12,32);
            dasm_str = self.build_dasm('lui', rd, rs1, rs2, 
                                       immi, imms, immb, immj, immu);

        elif (instr_bin[0:7] == '1100111'):
            # ECALL
            if (instr_bin[7:] == '0000000000000000000000000'):
                dasm_str = self.build_dasm('ecall', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);
            # ECALL
            if (instr_bin[7:] == '0000000000000100000000000'):
                eop = True;
                dasm_str = self.build_dasm('ebreak', rd, rs1, rs2, 
                                           immi, imms, immb, immj, immu);

        # Natural PC sum
        if (not(change_pc)):
            self.pc = self.pc + 4;

        # Force X0 to 0
        if (self.rf[0] != 0):
            self.rf[0] = 0;

        # Generate first log section
        log_str = self.print_log(pc_cur, instr, rd, rs1, rs2, rs1_old, rs2_old);

        #print (f'{log_str} {dasm_str}');
        self.log = self.log + f'{log_str} {dasm_str}\n';

        # DEBUG
        #a = input();

        return eop;

        ## DBG
        #print(f'RD: {self.rf[rd]}')
        #print(f'R1: {self.rf[rs1]}')
        #print(f'R2: {self.rf[rs2]}')


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

    def print_log (self, pc, instr, rd, rs1, rs2, rs1_old, rs2_old):
        pc_hex = hex(pc)[2:].zfill(8).upper();
        instr_hex = instr.upper();
        rd_cont = hex(self.usig_word(self.rf[rd]))[2:].zfill(8).upper();
        rs1_cont = hex(self.usig_word(rs1_old))[2:].zfill(8).upper();
        rs2_cont = hex(self.usig_word(rs2_old))[2:].zfill(8).upper();

        # Construct full string:
        log_str = f'PC={pc_hex} ';
        log_str = log_str + f'[{instr_hex}] ';
        log_str = log_str + f'x{self.align_zero(rd)}={rd_cont} ';
        log_str = log_str + f'x{self.align_zero(rs1)}={rs1_cont} ';
        log_str = log_str + f'x{self.align_zero(rs2)}={rs2_cont} ';

        return log_str;


    def align_zero (self, value):
        if (value < 10):
            return f'0{value}';
        else:
            return str(value);

    
    def get_log_name (self, dump_path):
        dump_lst = dump_path.split('/');
        file_nm = dump_lst[-1];
        file_lst = file_nm.split('.');
        
        return f'{file_lst[0]}.{file_lst[1]}.log'; 


    # Build deassembly print 
    def build_dasm (self, mn, rd, rs1, rs2, immi, imms, immb, immj, immu):
        instr_args_list = list();
        if (mn == 'and' or mn == 'or' or mn == 'sra' or mn == 'srl' or \
            mn == 'xor' or mn == 'sltu' or mn == 'slt' or mn == 'sll' or \
            mn == 'sub' or mn == 'add' or mn == 'mul' or mn == 'mulh' or \
            mn == 'mulhsu' or mn == 'mulhu' or mn == 'div' or mn == 'divu' or \
            mn == 'rem' or mn == 'remu'):
            
            return f'{mn.ljust(8)}{self.abi_list[rd]},{self.abi_list[rs1]},{self.abi_list[rs2]}';

        elif (mn == 'lui' or mn == 'auipc'):

            # TODO: Check the IMMU representation (signed or unsigned)
            return f'{mn.ljust(8)}{self.abi_list[rd]},{immu}';

        elif (mn == 'beq' or mn == 'bne' or mn == 'blt' or mn == 'bge' or \
              mn == 'bltu' or mn == 'bgeu'):
        
            signed_immb = self.sign_extend(immb,13);
            return f'{mn.ljust(8)}{self.abi_list[rs1]},{self.abi_list[rs2]},{signed_immb}';

        elif (mn == 'jal'):

            signed_immj = self.sign_extend(immj,21);
            return f'{mn.ljust(8)}{self.abi_list[rd]},{signed_immj}';

        elif (mn == 'jalr'):

            signed_immi = self.sign_extend(immi,12);
            return f'{mn.ljust(8)}{self.abi_list[rd]},{self.abi_list[rs1]},{signed_immi}';

        elif (mn == 'lb' or mn == 'lh' or mn == 'lw' or \
              mn == 'lbu' or mn == 'lhu'):

            signed_immi = self.sign_extend(immi,12);
            return f'{mn.ljust(8)}{self.abi_list[rd]},{signed_immi}({self.abi_list[rs1]})';

        elif (mn == 'addi' or mn == 'slti' or \
              mn == 'sltiu' or mn == 'xori' or mn == 'ori' or mn == 'andi'):

            signed_immi = self.sign_extend(immi,12);
            return f'{mn.ljust(8)}{self.abi_list[rd]},{self.abi_list[rs1]},{signed_immi}';

        elif (mn == 'sb' or mn == 'sh' or mn == 'sw'):

            signed_imms = self.sign_extend(imms,12);
            return f'{mn.ljust(8)}{self.abi_list[rs2]},{signed_imms}({self.abi_list[rs1]})';

        elif (mn == 'slli' or mn == 'srli' or mn == 'srai'):

            return f'{mn.ljust(8)}{self.abi_list[rd]},{self.abi_list[rs1]},{rs2}';

        elif (mn == 'ecall' or mn == 'ebreak'):

            return f'{mn.ljust(8)}';
