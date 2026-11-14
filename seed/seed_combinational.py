"""Combinational seed designs for the coverage knowledge base."""

E = []


def add(eid, dtype, width, module, signals, req, rtl, cg):
    E.append(dict(id=eid, design_context=dict(module=module, data_width=width, type=dtype),
                  signals=signals, english_requirement=req, rtl=rtl, coverage_model=cg))


add("mux8_1bit_001", "8-to-1 multiplexer", 8, "MUX8", ["d", "sel", "y"],
    "Cover 8-to-1 multiplexer behavior for every select value, toggling of each data input bit, and the output value observed for each select.",
    """module mux8(d, sel, y);
  input [7:0] d;
  input [2:0] sel;
  output y;
  assign y = d[sel];
endmodule""",
    """covergroup cg_mux8 (ref logic [7:0] d, ref logic [2:0] sel, ref logic y);
  sel_cp : coverpoint sel {
    bins s[] = {[0:7]};
  }
  y_cp : coverpoint y {
    bins y_0 = {0};
    bins y_1 = {1};
  }
  sel_x_y : cross sel_cp, y_cp;
endgroup""")

add("decoder3to8_3bit_001", "3-to-8 decoder", 3, "DECODER3TO8", ["sel", "en", "y"],
    "Cover 3-to-8 decoder behavior for all select values with the enable asserted, the all-zero output when enable is deasserted, and the cross of select against enable.",
    """module decoder3to8(sel, en, y);
  input [2:0] sel;
  input en;
  output [7:0] y;
  assign y = en ? (8'b0000_0001 << sel) : 8'b0;
endmodule""",
    """covergroup cg_dec38 (ref logic [2:0] sel, ref logic en, ref logic [7:0] y);
  sel_cp : coverpoint sel {
    bins s[] = {[0:7]};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  y_cp : coverpoint y {
    bins onehot[] = {8'h01, 8'h02, 8'h04, 8'h08, 8'h10, 8'h20, 8'h40, 8'h80};
    bins zero     = {8'h00};
  }
  sel_x_en : cross sel_cp, en_cp;
endgroup""")

add("encoder8to3_8bit_001", "8-to-3 binary encoder", 8, "ENCODER8TO3", ["d", "y", "valid"],
    "Cover 8-to-3 encoder behavior for each one-hot input, the encoded output value for each, and the valid flag in both asserted and deasserted states.",
    """module encoder8to3(d, y, valid);
  input [7:0] d;
  output reg [2:0] y;
  output valid;
  assign valid = |d;
  always @(*) begin
    case (d)
      8'h01: y = 3'd0;
      8'h02: y = 3'd1;
      8'h04: y = 3'd2;
      8'h08: y = 3'd3;
      8'h10: y = 3'd4;
      8'h20: y = 3'd5;
      8'h40: y = 3'd6;
      8'h80: y = 3'd7;
      default: y = 3'd0;
    endcase
  end
endmodule""",
    """covergroup cg_enc83 (ref logic [7:0] d, ref logic [2:0] y, ref logic valid);
  d_cp : coverpoint d {
    bins onehot[] = {8'h01, 8'h02, 8'h04, 8'h08, 8'h10, 8'h20, 8'h40, 8'h80};
    bins zero     = {8'h00};
  }
  y_cp : coverpoint y {
    bins code[] = {[0:7]};
  }
  valid_cp : coverpoint valid {
    bins invalid = {0};
    bins ok      = {1};
  }
  y_x_valid : cross y_cp, valid_cp;
endgroup""")

add("adder4_4bit_001", "4-bit adder with carry", 4, "ADDER4", ["a", "b", "cin", "sum", "cout"],
    "Cover 4-bit adder behavior across the full input range for both operands, both carry-in states, and the carry-out asserted and deasserted, crossing carry-in against carry-out.",
    """module adder4(a, b, cin, sum, cout);
  input [3:0] a, b;
  input cin;
  output [3:0] sum;
  output cout;
  assign {cout, sum} = a + b + cin;
endmodule""",
    """covergroup cg_adder4 (ref logic [3:0] a, b, sum, ref logic cin, cout);
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  cin_cp : coverpoint cin {
    bins no_carry = {0};
    bins carry    = {1};
  }
  cout_cp : coverpoint cout {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  a_x_b     : cross a_cp, b_cp;
  cin_x_cout: cross cin_cp, cout_cp;
endgroup""")

add("adder32_32bit_001", "32-bit adder", 32, "ADDER32", ["a", "b", "sum", "cout"],
    "Cover 32-bit adder behavior across low, mid, and high value ranges for both operands and the sum, including zero and maximum boundaries, and the overflow carry-out in both states.",
    """module adder32(a, b, sum, cout);
  input [31:0] a, b;
  output [31:0] sum;
  output cout;
  assign {cout, sum} = a + b;
endmodule""",
    """covergroup cg_adder32 (ref logic [31:0] a, b, sum, ref logic cout);
  a_cp : coverpoint a {
    bins zero = {0};
    bins low  = {[1:32'h0000_FFFF]};
    bins high = {[32'h0001_0000:32'hFFFF_FFFE]};
    bins max  = {32'hFFFF_FFFF};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins low  = {[1:32'h0000_FFFF]};
    bins high = {[32'h0001_0000:32'hFFFF_FFFE]};
    bins max  = {32'hFFFF_FFFF};
  }
  sum_cp : coverpoint sum {
    bins zero = {0};
    bins mid  = {[1:32'hFFFF_FFFE]};
    bins max  = {32'hFFFF_FFFF};
  }
  cout_cp : coverpoint cout {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  a_x_b : cross a_cp, b_cp;
endgroup""")

add("sub8_8bit_001", "8-bit subtractor", 8, "SUB8", ["a", "b", "diff", "borrow"],
    "Cover 8-bit subtractor behavior for operand ranges, the zero and maximum difference values, and the borrow output asserted when the subtrahend exceeds the minuend.",
    """module sub8(a, b, diff, borrow);
  input [7:0] a, b;
  output [7:0] diff;
  output borrow;
  assign {borrow, diff} = a - b;
endmodule""",
    """covergroup cg_sub8 (ref logic [7:0] a, b, diff, ref logic borrow);
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  diff_cp : coverpoint diff {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  borrow_cp : coverpoint borrow {
    bins no_borrow = {0};
    bins borrowed  = {1};
  }
  a_x_borrow : cross a_cp, borrow_cp;
endgroup""")

add("comparator8_8bit_001", "8-bit magnitude comparator", 8, "COMPARATOR8",
    ["a", "b", "gt", "eq", "lt"],
    "Cover 8-bit comparator behavior for the greater-than, equal, and less-than outputs, ensuring each is asserted at least once and that exactly one is active per comparison.",
    """module comparator8(a, b, gt, eq, lt);
  input [7:0] a, b;
  output gt, eq, lt;
  assign gt = (a > b);
  assign eq = (a == b);
  assign lt = (a < b);
endmodule""",
    """covergroup cg_cmp8 (ref logic [7:0] a, b, ref logic gt, eq, lt);
  a_cp : coverpoint a {
    bins low  = {[0:84]};
    bins mid  = {[85:169]};
    bins high = {[170:255]};
  }
  b_cp : coverpoint b {
    bins low  = {[0:84]};
    bins mid  = {[85:169]};
    bins high = {[170:255]};
  }
  result_cp : coverpoint {gt, eq, lt} {
    bins is_gt = {3'b100};
    bins is_eq = {3'b010};
    bins is_lt = {3'b001};
    illegal_bins impossible = default;
  }
  a_x_b : cross a_cp, b_cp;
endgroup""")

add("alu8_8bit_001", "8-bit ALU", 8, "ALU8", ["a", "b", "op", "result", "zero"],
    "Cover 8-bit ALU behavior for every opcode, operand value ranges, the zero flag in both states, and the cross of opcode against the zero flag to confirm each operation can produce zero.",
    """module alu8(a, b, op, result, zero);
  input [7:0] a, b;
  input [2:0] op;
  output reg [7:0] result;
  output zero;
  assign zero = (result == 8'b0);
  always @(*) begin
    case (op)
      3'd0: result = a + b;
      3'd1: result = a - b;
      3'd2: result = a & b;
      3'd3: result = a | b;
      3'd4: result = a ^ b;
      3'd5: result = ~a;
      3'd6: result = a << 1;
      3'd7: result = a >> 1;
    endcase
  end
endmodule""",
    """covergroup cg_alu8 (ref logic [7:0] a, b, result, ref logic [2:0] op, ref logic zero);
  op_cp : coverpoint op {
    bins op_add = {0};
    bins op_sub = {1};
    bins op_and = {2};
    bins op_or  = {3};
    bins op_xor = {4};
    bins op_not = {5};
    bins op_shl = {6};
    bins op_shr = {7};
  }
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  result_cp : coverpoint result {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  zero_cp : coverpoint zero {
    bins nonzero = {0};
    bins is_zero = {1};
  }
  op_x_zero : cross op_cp, zero_cp;
  op_x_a    : cross op_cp, a_cp;
endgroup""")

add("barrel_shift8_8bit_001", "8-bit barrel shifter", 8, "BARREL_SHIFT8",
    ["din", "shamt", "dir", "dout"],
    "Cover 8-bit barrel shifter behavior for every shift amount including zero and maximum, both shift directions, and the cross of direction against shift amount.",
    """module barrel_shift8(din, shamt, dir, dout);
  input [7:0] din;
  input [2:0] shamt;
  input dir;
  output [7:0] dout;
  assign dout = dir ? (din >> shamt) : (din << shamt);
endmodule""",
    """covergroup cg_barrel (ref logic [7:0] din, dout, ref logic [2:0] shamt, ref logic dir);
  shamt_cp : coverpoint shamt {
    bins no_shift = {0};
    bins small_sh  = {[1:3]};
    bins large_sh  = {[4:7]};
  }
  dir_cp : coverpoint dir {
    bins left  = {0};
    bins right = {1};
  }
  dout_cp : coverpoint dout {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  dir_x_shamt : cross dir_cp, shamt_cp;
endgroup""")

add("parity8_8bit_001", "8-bit parity generator", 8, "PARITY8", ["din", "even", "odd"],
    "Cover 8-bit parity generator behavior for both even and odd parity results, the all-zero and all-one inputs, and inputs across a spread of set-bit counts.",
    """module parity8(din, even, odd);
  input [7:0] din;
  output even, odd;
  assign odd  = ^din;
  assign even = ~(^din);
endmodule""",
    """covergroup cg_parity8 (ref logic [7:0] din, ref logic even, odd);
  din_cp : coverpoint din {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins low      = {[8'h01:8'h7F]};
    bins high     = {[8'h80:8'hFE]};
  }
  odd_cp : coverpoint odd {
    bins even_parity = {0};
    bins odd_parity  = {1};
  }
  din_x_odd : cross din_cp, odd_cp;
endgroup""")

add("majority3_1bit_001", "3-input majority voter", 1, "MAJORITY3", ["a", "b", "c", "y"],
    "Cover the 3-input majority voter for all eight input combinations and both output values, confirming the output follows the majority of the inputs.",
    """module majority3(a, b, c, y);
  input a, b, c;
  output y;
  assign y = (a & b) | (b & c) | (a & c);
endmodule""",
    """covergroup cg_maj3 (ref logic a, b, c, y);
  abc_cp : coverpoint {a, b, c} {
    bins combo[] = {[3'b000:3'b111]};
  }
  y_cp : coverpoint y {
    bins minority = {0};
    bins majority = {1};
  }
  abc_x_y : cross abc_cp, y_cp;
endgroup""")

add("bin2gray_4bit_001", "4-bit binary to Gray converter", 4, "BIN2GRAY", ["bin", "gray"],
    "Cover 4-bit binary-to-Gray conversion across the full input range including the zero and maximum values, and confirm every Gray output code is produced.",
    """module bin2gray(bin, gray);
  input [3:0] bin;
  output [3:0] gray;
  assign gray = bin ^ (bin >> 1);
endmodule""",
    """covergroup cg_b2g (ref logic [3:0] bin, gray);
  bin_cp : coverpoint bin {
    bins value[] = {[0:15]};
  }
  gray_cp : coverpoint gray {
    bins code[] = {[0:15]};
  }
endgroup""")

add("gray2bin_4bit_001", "4-bit Gray to binary converter", 4, "GRAY2BIN", ["gray", "bin"],
    "Cover 4-bit Gray-to-binary conversion for every Gray input code and confirm the full range of binary outputs is produced.",
    """module gray2bin(gray, bin);
  input [3:0] gray;
  output [3:0] bin;
  assign bin[3] = gray[3];
  assign bin[2] = gray[3] ^ gray[2];
  assign bin[1] = gray[3] ^ gray[2] ^ gray[1];
  assign bin[0] = gray[3] ^ gray[2] ^ gray[1] ^ gray[0];
endmodule""",
    """covergroup cg_g2b (ref logic [3:0] gray, bin);
  gray_cp : coverpoint gray {
    bins code[] = {[0:15]};
  }
  bin_cp : coverpoint bin {
    bins value[] = {[0:15]};
  }
endgroup""")

add("bcd_adder_4bit_001", "BCD adder", 4, "BCD_ADDER", ["a", "b", "cin", "sum", "cout"],
    "Cover BCD adder behavior for all valid decimal digit operands, both carry-in states, the carry-out generated when the result exceeds nine, and treat non-decimal operand values as illegal.",
    """module bcd_adder(a, b, cin, sum, cout);
  input [3:0] a, b;
  input cin;
  output reg [3:0] sum;
  output reg cout;
  reg [4:0] tmp;
  always @(*) begin
    tmp = a + b + cin;
    if (tmp > 9) begin
      sum  = tmp - 10;
      cout = 1'b1;
    end else begin
      sum  = tmp[3:0];
      cout = 1'b0;
    end
  end
endmodule""",
    """covergroup cg_bcd_add (ref logic [3:0] a, b, sum, ref logic cin, cout);
  a_cp : coverpoint a {
    bins digit[] = {[0:9]};
    illegal_bins non_bcd = {[10:15]};
  }
  b_cp : coverpoint b {
    bins digit[] = {[0:9]};
    illegal_bins non_bcd = {[10:15]};
  }
  cin_cp : coverpoint cin {
    bins no_carry = {0};
    bins carry    = {1};
  }
  cout_cp : coverpoint cout {
    bins no_carry = {0};
    bins carry    = {1};
  }
  a_x_b     : cross a_cp, b_cp;
  cin_x_cout: cross cin_cp, cout_cp;
endgroup""")

add("seven_seg_4bit_001", "seven-segment decoder", 4, "SEVEN_SEG", ["bcd", "seg"],
    "Cover the seven-segment decoder for all ten decimal digit inputs, the blanked output for invalid inputs, and confirm each distinct segment pattern is produced.",
    """module seven_seg(bcd, seg);
  input [3:0] bcd;
  output reg [6:0] seg;
  always @(*) begin
    case (bcd)
      4'd0: seg = 7'b1111110;
      4'd1: seg = 7'b0110000;
      4'd2: seg = 7'b1101101;
      4'd3: seg = 7'b1111001;
      4'd4: seg = 7'b0110011;
      4'd5: seg = 7'b1011011;
      4'd6: seg = 7'b1011111;
      4'd7: seg = 7'b1110000;
      4'd8: seg = 7'b1111111;
      4'd9: seg = 7'b1111011;
      default: seg = 7'b0000000;
    endcase
  end
endmodule""",
    """covergroup cg_7seg (ref logic [3:0] bcd, ref logic [6:0] seg);
  bcd_cp : coverpoint bcd {
    bins digit[]  = {[0:9]};
    bins invalid  = {[10:15]};
  }
  seg_cp : coverpoint seg {
    bins blank = {7'b0000000};
    bins lit   = {[7'b0000001:7'b1111111]};
  }
  bcd_x_seg : cross bcd_cp, seg_cp;
endgroup""")

add("popcount8_8bit_001", "8-bit population counter", 8, "POPCOUNT8", ["din", "count"],
    "Cover the 8-bit population counter for every possible set-bit count from zero through eight, including the all-zero and all-one inputs.",
    """module popcount8(din, count);
  input [7:0] din;
  output [3:0] count;
  assign count = din[0] + din[1] + din[2] + din[3] +
                 din[4] + din[5] + din[6] + din[7];
endmodule""",
    """covergroup cg_popcount (ref logic [7:0] din, ref logic [3:0] count);
  din_cp : coverpoint din {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins others   = {[8'h01:8'hFE]};
  }
  count_cp : coverpoint count {
    bins n[] = {[0:8]};
    illegal_bins impossible = {[9:15]};
  }
endgroup""")

add("onehot_det_8bit_001", "one-hot detector", 8, "ONEHOT_DET", ["din", "is_onehot"],
    "Cover the one-hot detector for genuine one-hot inputs, the all-zero input, and multi-bit inputs, crossing the input class against the detector output.",
    """module onehot_det(din, is_onehot);
  input [7:0] din;
  output is_onehot;
  assign is_onehot = (din != 8'b0) && ((din & (din - 1)) == 8'b0);
endmodule""",
    """covergroup cg_onehot (ref logic [7:0] din, ref logic is_onehot);
  din_cp : coverpoint din {
    bins onehot[]  = {8'h01, 8'h02, 8'h04, 8'h08, 8'h10, 8'h20, 8'h40, 8'h80};
    bins zero      = {8'h00};
    bins multi     = {[8'h03:8'h07], [8'h09:8'h0F]};
  }
  det_cp : coverpoint is_onehot {
    bins not_onehot = {0};
    bins onehot     = {1};
  }
  din_x_det : cross din_cp, det_cp;
endgroup""")

add("abs8_8bit_001", "8-bit absolute value", 8, "ABS8", ["din", "dout"],
    "Cover the 8-bit absolute value unit for positive, negative, and zero inputs, including the most-negative input where the magnitude cannot be represented.",
    """module abs8(din, dout);
  input signed [7:0] din;
  output [7:0] dout;
  assign dout = din[7] ? (~din + 1'b1) : din;
endmodule""",
    """covergroup cg_abs8 (ref logic [7:0] din, dout);
  din_cp : coverpoint din {
    bins zero      = {8'h00};
    bins positive  = {[8'h01:8'h7F]};
    bins negative  = {[8'h81:8'hFF]};
    bins most_neg  = {8'h80};
  }
  dout_cp : coverpoint dout {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'h7F]};
    bins over = {8'h80};
  }
  din_x_dout : cross din_cp, dout_cp;
endgroup""")

add("minmax8_8bit_001", "8-bit min/max selector", 8, "MINMAX8", ["a", "b", "min_o", "max_o"],
    "Cover the min/max selector for cases where the first operand is larger, the second is larger, and the two are equal, across low and high operand ranges.",
    """module minmax8(a, b, min_o, max_o);
  input [7:0] a, b;
  output [7:0] min_o, max_o;
  assign min_o = (a < b) ? a : b;
  assign max_o = (a < b) ? b : a;
endmodule""",
    """covergroup cg_minmax (ref logic [7:0] a, b, min_o, max_o);
  a_cp : coverpoint a {
    bins low  = {[0:127]};
    bins high = {[128:255]};
  }
  b_cp : coverpoint b {
    bins low  = {[0:127]};
    bins high = {[128:255]};
  }
  a_x_b : cross a_cp, b_cp;
endgroup""")

add("sign_extend_001", "sign extension unit", 8, "SIGN_EXTEND", ["din", "dout"],
    "Cover the sign extension unit for positive and negative inputs, the zero input, and the extreme representable values, confirming the upper bits replicate the sign.",
    """module sign_extend(din, dout);
  input [7:0] din;
  output [15:0] dout;
  assign dout = {{8{din[7]}}, din};
endmodule""",
    """covergroup cg_sext (ref logic [7:0] din, ref logic [15:0] dout);
  din_cp : coverpoint din {
    bins zero     = {8'h00};
    bins positive = {[8'h01:8'h7F]};
    bins negative = {[8'h80:8'hFE]};
    bins neg_one  = {8'hFF};
  }
  sign_cp : coverpoint dout[15] {
    bins pos = {0};
    bins neg = {1};
  }
  din_x_sign : cross din_cp, sign_cp;
endgroup""")

add("mux2_en_1bit_001", "2-to-1 multiplexer with enable", 1, "MUX2_EN",
    ["a", "b", "sel", "en", "y"],
    "Cover the enabled 2-to-1 multiplexer for both select values and all data input combinations while enabled, and the forced-zero output while disabled.",
    """module mux2_en(a, b, sel, en, y);
  input a, b, sel, en;
  output y;
  assign y = en ? (sel ? b : a) : 1'b0;
endmodule""",
    """covergroup cg_mux2_en (ref logic a, b, sel, en, y);
  sel_cp : coverpoint sel {
    bins sel_a = {0};
    bins sel_b = {1};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  ab_cp : coverpoint {a, b} {
    bins ab[] = {[2'b00:2'b11]};
  }
  sel_x_en : cross sel_cp, en_cp;
  ab_x_sel : cross ab_cp, sel_cp;
endgroup""")

add("crossbar2x2_001", "2x2 crossbar switch", 2, "CROSSBAR2X2",
    ["in0", "in1", "swap", "out0", "out1"],
    "Cover the 2x2 crossbar for both the pass-through and swapped configurations across all input combinations, crossing the swap control against the input pattern.",
    """module crossbar2x2(in0, in1, swap, out0, out1);
  input [1:0] in0, in1;
  input swap;
  output [1:0] out0, out1;
  assign out0 = swap ? in1 : in0;
  assign out1 = swap ? in0 : in1;
endmodule""",
    """covergroup cg_xbar (ref logic [1:0] in0, in1, out0, out1, ref logic swap);
  swap_cp : coverpoint swap {
    bins pass    = {0};
    bins swapped = {1};
  }
  in0_cp : coverpoint in0 {
    bins v[] = {[0:3]};
  }
  in1_cp : coverpoint in1 {
    bins v[] = {[0:3]};
  }
  swap_x_in0 : cross swap_cp, in0_cp;
endgroup""")

add("lut4_001", "4-input lookup table", 4, "LUT4", ["addr", "config_bits", "dout"],
    "Cover the 4-input lookup table for every address value, and the output in both states, crossing address against output to confirm each table entry is exercised.",
    """module lut4(addr, config_bits, dout);
  input [3:0] addr;
  input [15:0] config_bits;
  output dout;
  assign dout = config_bits[addr];
endmodule""",
    """covergroup cg_lut4 (ref logic [3:0] addr, ref logic dout);
  addr_cp : coverpoint addr {
    bins entry[] = {[0:15]};
  }
  dout_cp : coverpoint dout {
    bins low  = {0};
    bins high = {1};
  }
  addr_x_dout : cross addr_cp, dout_cp;
endgroup""")

add("tristate_buf_001", "tri-state buffer", 8, "TRISTATE_BUF", ["din", "oe", "dout"],
    "Cover the tri-state buffer with the output enable asserted for a spread of data values and deasserted for the high-impedance state, crossing enable against data.",
    """module tristate_buf(din, oe, dout);
  input [7:0] din;
  input oe;
  output [7:0] dout;
  assign dout = oe ? din : 8'bz;
endmodule""",
    """covergroup cg_tribuf (ref logic [7:0] din, ref logic oe);
  oe_cp : coverpoint oe {
    bins hiz    = {0};
    bins driven = {1};
  }
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  oe_x_din : cross oe_cp, din_cp;
endgroup""")
