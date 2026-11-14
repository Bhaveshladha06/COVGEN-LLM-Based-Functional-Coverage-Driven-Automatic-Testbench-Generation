"""Sequential seed designs (flip-flops, registers, counters, timing) for the
coverage knowledge base. These fill the gap that left every clocked design --
the counter in particular -- retrieving nothing from a purely combinational
corpus."""

E = []


def add(eid, dtype, width, module, signals, req, rtl, cg):
    E.append(dict(id=eid, design_context=dict(module=module, data_width=width, type=dtype),
                  signals=signals, english_requirement=req, rtl=rtl, coverage_model=cg))


add("dff_1bit_001", "D flip-flop with async reset", 1, "DFF",
    ["clk", "rst_n", "d", "q"],
    "Cover the D flip-flop capturing both data values on the clock edge, the asynchronous reset forcing the output low, and the transition of the output in both directions.",
    """module dff(clk, rst_n, d, q);
  input clk, rst_n, d;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else        q <= d;
  end
endmodule""",
    """covergroup cg_dff (ref logic d, q, rst_n) @(posedge clk);
  d_cp : coverpoint d {
    bins low  = {0};
    bins high = {1};
  }
  q_cp : coverpoint q {
    bins low  = {0};
    bins high = {1};
  }
  rst_cp : coverpoint rst_n {
    bins in_reset  = {0};
    bins out_reset = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  d_x_rst : cross d_cp, rst_cp;
endgroup""")

add("dff_en_1bit_001", "D flip-flop with clock enable", 1, "DFF_EN",
    ["clk", "rst_n", "en", "d", "q"],
    "Cover the enabled D flip-flop loading new data when the enable is asserted, holding its value when the enable is deasserted, and the cross of enable against data.",
    """module dff_en(clk, rst_n, en, d, q);
  input clk, rst_n, en, d;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)   q <= 1'b0;
    else if (en)  q <= d;
  end
endmodule""",
    """covergroup cg_dff_en (ref logic d, q, en) @(posedge clk);
  en_cp : coverpoint en {
    bins hold = {0};
    bins load = {1};
  }
  d_cp : coverpoint d {
    bins low  = {0};
    bins high = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise      = (0 => 1);
    bins fall      = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  en_x_d : cross en_cp, d_cp;
endgroup""")

add("tff_1bit_001", "T flip-flop", 1, "TFF", ["clk", "rst_n", "t", "q"],
    "Cover the T flip-flop toggling its output when the toggle input is asserted, holding when deasserted, and both output transition directions.",
    """module tff(clk, rst_n, t, q);
  input clk, rst_n, t;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else if (t) q <= ~q;
  end
endmodule""",
    """covergroup cg_tff (ref logic t, q) @(posedge clk);
  t_cp : coverpoint t {
    bins hold   = {0};
    bins toggle = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise      = (0 => 1);
    bins fall      = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  q_cp : coverpoint q {
    bins low  = {0};
    bins high = {1};
  }
  t_x_q : cross t_cp, q_cp;
endgroup""")

add("jkff_1bit_001", "JK flip-flop", 1, "JKFF", ["clk", "rst_n", "j", "k", "q"],
    "Cover the JK flip-flop across all four input combinations covering hold, reset, set, and toggle behaviour, and both output transition directions.",
    """module jkff(clk, rst_n, j, k, q);
  input clk, rst_n, j, k;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else begin
      case ({j, k})
        2'b00: q <= q;
        2'b01: q <= 1'b0;
        2'b10: q <= 1'b1;
        2'b11: q <= ~q;
      endcase
    end
  end
endmodule""",
    """covergroup cg_jkff (ref logic j, k, q) @(posedge clk);
  jk_cp : coverpoint {j, k} {
    bins hold   = {2'b00};
    bins clear  = {2'b01};
    bins set    = {2'b10};
    bins toggle = {2'b11};
  }
  q_cp : coverpoint q {
    bins low  = {0};
    bins high = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
  }
  jk_x_q : cross jk_cp, q_cp;
endgroup""")

add("reg8_8bit_001", "8-bit register with load", 8, "REG8",
    ["clk", "rst_n", "load", "din", "dout"],
    "Cover the 8-bit register loading data across value ranges, holding its contents when load is deasserted, the reset-to-zero behaviour, and the cross of load against data range.",
    """module reg8(clk, rst_n, load, din, dout);
  input clk, rst_n, load;
  input [7:0] din;
  output reg [7:0] dout;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)    dout <= 8'b0;
    else if (load) dout <= din;
  end
endmodule""",
    """covergroup cg_reg8 (ref logic [7:0] din, dout, ref logic load) @(posedge clk);
  load_cp : coverpoint load {
    bins hold = {0};
    bins load = {1};
  }
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  dout_cp : coverpoint dout {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  load_x_din : cross load_cp, din_cp;
endgroup""")

add("shift_reg_l_8bit_001", "8-bit left shift register", 8, "SHIFT_REG_L",
    ["clk", "rst_n", "sin", "dout"],
    "Cover the left shift register serially loading both bit values, the all-zero and all-one register states, and the serial output bit shifting out in both states.",
    """module shift_reg_l(clk, rst_n, sin, dout);
  input clk, rst_n, sin;
  output reg [7:0] dout;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) dout <= 8'b0;
    else        dout <= {dout[6:0], sin};
  end
endmodule""",
    """covergroup cg_shift_l (ref logic [7:0] dout, ref logic sin) @(posedge clk);
  sin_cp : coverpoint sin {
    bins shift_zero = {0};
    bins shift_one  = {1};
  }
  dout_cp : coverpoint dout {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins mid      = {[8'h01:8'hFE]};
  }
  msb_cp : coverpoint dout[7] {
    bins low  = {0};
    bins high = {1};
  }
  sin_x_dout : cross sin_cp, dout_cp;
endgroup""")

add("shift_reg_bidir_8bit_001", "8-bit bidirectional shift register", 8, "SHIFT_REG_BIDIR",
    ["clk", "rst_n", "dir", "en", "sin", "dout"],
    "Cover the bidirectional shift register shifting in both directions, holding when disabled, and the cross of direction against enable to confirm every mode is exercised.",
    """module shift_reg_bidir(clk, rst_n, dir, en, sin, dout);
  input clk, rst_n, dir, en, sin;
  output reg [7:0] dout;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)   dout <= 8'b0;
    else if (en)  dout <= dir ? {sin, dout[7:1]} : {dout[6:0], sin};
  end
endmodule""",
    """covergroup cg_shift_bidir (ref logic [7:0] dout, ref logic dir, en, sin) @(posedge clk);
  dir_cp : coverpoint dir {
    bins left  = {0};
    bins right = {1};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins shift = {1};
  }
  sin_cp : coverpoint sin {
    bins zero = {0};
    bins one  = {1};
  }
  dir_x_en  : cross dir_cp, en_cp;
  dir_x_sin : cross dir_cp, sin_cp;
endgroup""")

add("counter_up8_8bit_001", "8-bit up counter", 8, "COUNTER_UP8",
    ["clk", "rst_n", "en", "count"],
    "Cover the 8-bit up counter reaching its maximum value and wrapping around to zero on the next enabled clock edge, holding its value while the enable is deasserted, and the reset returning the count to zero.",
    """module counter_up8(clk, rst_n, en, count);
  input clk, rst_n, en;
  output reg [7:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 8'b0;
    else if (en) count <= count + 1'b1;
  end
endmodule""",
    """covergroup cg_cnt_up8 (ref logic [7:0] count, ref logic en, rst_n) @(posedge clk);
  count_cp : coverpoint count {
    bins zero = {8'h00};
    bins low  = {[8'h01:8'h7F]};
    bins high = {[8'h80:8'hFE]};
    bins max  = {8'hFF};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  rst_cp : coverpoint rst_n {
    bins asserted  = {0};
    bins deasserted= {1};
  }
  count_trans_cp : coverpoint count {
    bins wrap      = (8'hFF => 8'h00);
    bins hold_zero = (8'h00 => 8'h00);
    bins hold_max  = (8'hFF => 8'hFF);
  }
  count_x_en : cross count_cp, en_cp;
  en_x_rst   : cross en_cp, rst_cp;
endgroup""")

add("counter_down4_4bit_001", "4-bit down counter", 4, "COUNTER_DOWN4",
    ["clk", "rst_n", "en", "count", "zero"],
    "Cover the 4-bit down counter decrementing to zero, underflowing from zero back to the maximum value, the zero flag asserting, and holding while disabled.",
    """module counter_down4(clk, rst_n, en, count, zero);
  input clk, rst_n, en;
  output reg [3:0] count;
  output zero;
  assign zero = (count == 4'b0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'hF;
    else if (en) count <= count - 1'b1;
  end
endmodule""",
    """covergroup cg_cnt_dn4 (ref logic [3:0] count, ref logic en, zero) @(posedge clk);
  count_cp : coverpoint count {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  zero_cp : coverpoint zero {
    bins nonzero = {0};
    bins at_zero = {1};
  }
  count_trans_cp : coverpoint count {
    bins underflow = (0 => 15);
    bins to_zero   = (1 => 0);
    bins hold_zero = (0 => 0);
  }
  count_x_en : cross count_cp, en_cp;
endgroup""")

add("counter_updown_4bit_001", "4-bit up/down counter", 4, "COUNTER_UPDOWN",
    ["clk", "rst_n", "en", "up", "count"],
    "Cover the up/down counter counting in both directions, wrapping at the maximum when counting up and underflowing at zero when counting down, and the cross of direction against enable.",
    """module counter_updown(clk, rst_n, en, up, count);
  input clk, rst_n, en, up;
  output reg [3:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0;
    else if (en) count <= up ? (count + 1'b1) : (count - 1'b1);
  end
endmodule""",
    """covergroup cg_cnt_ud (ref logic [3:0] count, ref logic en, up) @(posedge clk);
  count_cp : coverpoint count {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  up_cp : coverpoint up {
    bins counting_down = {0};
    bins counting_up   = {1};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  count_trans_cp : coverpoint count {
    bins wrap_up   = (15 => 0);
    bins wrap_down = (0 => 15);
  }
  up_x_en    : cross up_cp, en_cp;
  count_x_up : cross count_cp, up_cp;
endgroup""")

add("counter_modn_4bit_001", "modulo-N counter", 4, "COUNTER_MODN",
    ["clk", "rst_n", "en", "count", "tc"],
    "Cover the modulo-N counter reaching its terminal count, rolling over to zero, asserting the terminal count flag, and holding while the enable is deasserted.",
    """module counter_modn(clk, rst_n, en, count, tc);
  input clk, rst_n, en;
  output reg [3:0] count;
  output tc;
  parameter N = 10;
  assign tc = (count == N - 1);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0;
    else if (en) count <= tc ? 4'b0 : (count + 1'b1);
  end
endmodule""",
    """covergroup cg_cnt_modn (ref logic [3:0] count, ref logic en, tc) @(posedge clk);
  count_cp : coverpoint count {
    bins zero     = {0};
    bins mid      = {[1:8]};
    bins terminal = {9};
    illegal_bins out_of_range = {[10:15]};
  }
  tc_cp : coverpoint tc {
    bins not_terminal = {0};
    bins terminal     = {1};
  }
  count_trans_cp : coverpoint count {
    bins rollover = (9 => 0);
    bins step     = (0 => 1);
  }
  count_x_tc : cross count_cp, tc_cp;
endgroup""")

add("ring_counter_4bit_001", "4-bit ring counter", 4, "RING_COUNTER",
    ["clk", "rst_n", "en", "count"],
    "Cover the ring counter visiting every one-hot state, completing a full rotation back to the initial state, and treating any non-one-hot state as illegal.",
    """module ring_counter(clk, rst_n, en, count);
  input clk, rst_n, en;
  output reg [3:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0001;
    else if (en) count <= {count[2:0], count[3]};
  end
endmodule""",
    """covergroup cg_ring (ref logic [3:0] count, ref logic en) @(posedge clk);
  count_cp : coverpoint count {
    bins s0 = {4'b0001};
    bins s1 = {4'b0010};
    bins s2 = {4'b0100};
    bins s3 = {4'b1000};
    illegal_bins not_onehot = default;
  }
  en_cp : coverpoint en {
    bins hold   = {0};
    bins rotate = {1};
  }
  count_trans_cp : coverpoint count {
    bins rot0 = (4'b0001 => 4'b0010);
    bins rot1 = (4'b0010 => 4'b0100);
    bins rot2 = (4'b0100 => 4'b1000);
    bins rot3 = (4'b1000 => 4'b0001);
  }
  count_x_en : cross count_cp, en_cp;
endgroup""")

add("johnson_counter_4bit_001", "4-bit Johnson counter", 4, "JOHNSON_COUNTER",
    ["clk", "rst_n", "en", "count"],
    "Cover the Johnson counter visiting all eight valid states in its sequence, completing a full cycle, and holding while the enable is deasserted.",
    """module johnson_counter(clk, rst_n, en, count);
  input clk, rst_n, en;
  output reg [3:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'b0000;
    else if (en) count <= {~count[0], count[3:1]};
  end
endmodule""",
    """covergroup cg_johnson (ref logic [3:0] count, ref logic en) @(posedge clk);
  count_cp : coverpoint count {
    bins valid[] = {4'b0000, 4'b1000, 4'b1100, 4'b1110,
                    4'b1111, 4'b0111, 4'b0011, 4'b0001};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins shift = {1};
  }
  count_trans_cp : coverpoint count {
    bins fill_start  = (4'b0000 => 4'b1000);
    bins fill_done   = (4'b1110 => 4'b1111);
    bins empty_start = (4'b1111 => 4'b0111);
    bins empty_done  = (4'b0001 => 4'b0000);
  }
  count_x_en : cross count_cp, en_cp;
endgroup""")

add("gray_counter_4bit_001", "4-bit Gray code counter", 4, "GRAY_COUNTER",
    ["clk", "rst_n", "en", "gray"],
    "Cover the Gray counter producing every Gray code value, wrapping from the last code back to zero, and holding while disabled, confirming only one bit changes per step.",
    """module gray_counter(clk, rst_n, en, gray);
  input clk, rst_n, en;
  output [3:0] gray;
  reg [3:0] bin;
  assign gray = bin ^ (bin >> 1);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  bin <= 4'b0;
    else if (en) bin <= bin + 1'b1;
  end
endmodule""",
    """covergroup cg_gray_cnt (ref logic [3:0] gray, ref logic en) @(posedge clk);
  gray_cp : coverpoint gray {
    bins code[] = {[0:15]};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins count = {1};
  }
  gray_trans_cp : coverpoint gray {
    bins first_step = (4'b0000 => 4'b0001);
    bins wrap       = (4'b1000 => 4'b0000);
  }
  gray_x_en : cross gray_cp, en_cp;
endgroup""")

add("bcd_counter_4bit_001", "BCD decade counter", 4, "BCD_COUNTER",
    ["clk", "rst_n", "en", "count", "carry"],
    "Cover the BCD decade counter visiting every decimal digit, rolling over from nine to zero, asserting the carry output on rollover, and never entering a non-decimal state.",
    """module bcd_counter(clk, rst_n, en, count, carry);
  input clk, rst_n, en;
  output reg [3:0] count;
  output carry;
  assign carry = en && (count == 4'd9);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'd0;
    else if (en) count <= (count == 4'd9) ? 4'd0 : (count + 1'b1);
  end
endmodule""",
    """covergroup cg_bcd_cnt (ref logic [3:0] count, ref logic en, carry) @(posedge clk);
  count_cp : coverpoint count {
    bins digit[] = {[0:9]};
    illegal_bins non_bcd = {[10:15]};
  }
  carry_cp : coverpoint carry {
    bins no_carry = {0};
    bins carry    = {1};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins count = {1};
  }
  count_trans_cp : coverpoint count {
    bins rollover = (9 => 0);
    bins step     = (0 => 1);
  }
  count_x_carry : cross count_cp, carry_cp;
endgroup""")

add("lfsr8_8bit_001", "8-bit LFSR", 8, "LFSR8", ["clk", "rst_n", "en", "lfsr"],
    "Cover the 8-bit linear feedback shift register producing values across its range, the seed value after reset, the feedback bit in both states, and the all-zero lock-up state treated as illegal.",
    """module lfsr8(clk, rst_n, en, lfsr);
  input clk, rst_n, en;
  output reg [7:0] lfsr;
  wire fb = lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  lfsr <= 8'hFF;
    else if (en) lfsr <= {lfsr[6:0], fb};
  end
endmodule""",
    """covergroup cg_lfsr8 (ref logic [7:0] lfsr, ref logic en) @(posedge clk);
  lfsr_cp : coverpoint lfsr {
    bins seed = {8'hFF};
    bins low  = {[8'h01:8'h7F]};
    bins high = {[8'h80:8'hFE]};
    illegal_bins lockup = {8'h00};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins shift = {1};
  }
  lsb_cp : coverpoint lfsr[0] {
    bins fb_zero = {0};
    bins fb_one  = {1};
  }
  lfsr_x_en : cross lfsr_cp, en_cp;
endgroup""")

add("accumulator_8bit_001", "8-bit accumulator", 8, "ACCUMULATOR",
    ["clk", "rst_n", "en", "din", "acc", "ovf"],
    "Cover the accumulator summing input values across ranges, holding when disabled, clearing on reset, and asserting the overflow flag when the accumulated total wraps.",
    """module accumulator(clk, rst_n, en, din, acc, ovf);
  input clk, rst_n, en;
  input [7:0] din;
  output reg [7:0] acc;
  output reg ovf;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc <= 8'b0;
      ovf <= 1'b0;
    end else if (en) begin
      {ovf, acc} <= acc + din;
    end
  end
endmodule""",
    """covergroup cg_accum (ref logic [7:0] din, acc, ref logic en, ovf) @(posedge clk);
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  acc_cp : coverpoint acc {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins accum = {1};
  }
  ovf_cp : coverpoint ovf {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  din_x_ovf : cross din_cp, ovf_cp;
  acc_x_en  : cross acc_cp, en_cp;
endgroup""")

add("edge_detect_1bit_001", "edge detector", 1, "EDGE_DETECT",
    ["clk", "rst_n", "din", "rise", "fall"],
    "Cover the edge detector asserting the rising-edge pulse on a low-to-high input transition and the falling-edge pulse on a high-to-low transition, with neither asserted while the input is steady.",
    """module edge_detect(clk, rst_n, din, rise, fall);
  input clk, rst_n, din;
  output rise, fall;
  reg din_d;
  assign rise = din & ~din_d;
  assign fall = ~din & din_d;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) din_d <= 1'b0;
    else        din_d <= din;
  end
endmodule""",
    """covergroup cg_edge (ref logic din, rise, fall) @(posedge clk);
  din_cp : coverpoint din {
    bins low  = {0};
    bins high = {1};
  }
  pulse_cp : coverpoint {rise, fall} {
    bins steady  = {2'b00};
    bins falling = {2'b01};
    bins rising  = {2'b10};
    illegal_bins both = {2'b11};
  }
  din_trans_cp : coverpoint din {
    bins rise_edge = (0 => 1);
    bins fall_edge = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  din_x_pulse : cross din_cp, pulse_cp;
endgroup""")

add("debouncer_1bit_001", "switch debouncer", 1, "DEBOUNCER",
    ["clk", "rst_n", "noisy", "clean"],
    "Cover the debouncer holding its output stable while the input is bouncing, propagating a change only after the input has been stable for the full count, and both output states.",
    """module debouncer(clk, rst_n, noisy, clean);
  input clk, rst_n, noisy;
  output reg clean;
  reg [3:0] cnt;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cnt   <= 4'b0;
      clean <= 1'b0;
    end else if (noisy != clean) begin
      if (cnt == 4'hF) begin
        clean <= noisy;
        cnt   <= 4'b0;
      end else cnt <= cnt + 1'b1;
    end else cnt <= 4'b0;
  end
endmodule""",
    """covergroup cg_debounce (ref logic noisy, clean) @(posedge clk);
  noisy_cp : coverpoint noisy {
    bins low  = {0};
    bins high = {1};
  }
  clean_cp : coverpoint clean {
    bins low  = {0};
    bins high = {1};
  }
  clean_trans_cp : coverpoint clean {
    bins settle_high = (0 => 1);
    bins settle_low  = (1 => 0);
    bins stable_low  = (0 => 0);
    bins stable_high = (1 => 1);
  }
  noisy_x_clean : cross noisy_cp, clean_cp;
endgroup""")

add("pulse_gen_1bit_001", "single-cycle pulse generator", 1, "PULSE_GEN",
    ["clk", "rst_n", "trig", "pulse"],
    "Cover the pulse generator emitting exactly one cycle of output pulse per trigger assertion, remaining low while the trigger is held, and rearming after the trigger is released.",
    """module pulse_gen(clk, rst_n, trig, pulse);
  input clk, rst_n, trig;
  output pulse;
  reg trig_d;
  assign pulse = trig & ~trig_d;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) trig_d <= 1'b0;
    else        trig_d <= trig;
  end
endmodule""",
    """covergroup cg_pulse (ref logic trig, pulse) @(posedge clk);
  trig_cp : coverpoint trig {
    bins idle    = {0};
    bins asserted= {1};
  }
  pulse_cp : coverpoint pulse {
    bins low  = {0};
    bins high = {1};
  }
  pulse_trans_cp : coverpoint pulse {
    bins fire   = (0 => 1);
    bins retire = (1 => 0);
  }
  trig_x_pulse : cross trig_cp, pulse_cp;
endgroup""")

add("clk_div_001", "clock divider", 4, "CLK_DIV", ["clk", "rst_n", "en", "clk_out"],
    "Cover the clock divider producing both output phases, the internal divide counter across its full range, and the output toggling only while the enable is asserted.",
    """module clk_div(clk, rst_n, en, clk_out);
  input clk, rst_n, en;
  output reg clk_out;
  reg [3:0] cnt;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cnt     <= 4'b0;
      clk_out <= 1'b0;
    end else if (en) begin
      if (cnt == 4'hF) begin
        cnt     <= 4'b0;
        clk_out <= ~clk_out;
      end else cnt <= cnt + 1'b1;
    end
  end
endmodule""",
    """covergroup cg_clkdiv (ref logic [3:0] cnt, ref logic en, clk_out) @(posedge clk);
  cnt_cp : coverpoint cnt {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  en_cp : coverpoint en {
    bins stopped = {0};
    bins running = {1};
  }
  out_trans_cp : coverpoint clk_out {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
  }
  cnt_x_en : cross cnt_cp, en_cp;
endgroup""")

add("sync_2ff_1bit_001", "two flip-flop synchronizer", 1, "SYNC_2FF",
    ["clk", "rst_n", "async_in", "sync_out"],
    "Cover the two-stage synchronizer propagating both input values through to the output, and both output transition directions after the synchronization delay.",
    """module sync_2ff(clk, rst_n, async_in, sync_out);
  input clk, rst_n, async_in;
  output sync_out;
  reg s1, s2;
  assign sync_out = s2;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s1 <= 1'b0;
      s2 <= 1'b0;
    end else begin
      s1 <= async_in;
      s2 <= s1;
    end
  end
endmodule""",
    """covergroup cg_sync2ff (ref logic async_in, sync_out) @(posedge clk);
  in_cp : coverpoint async_in {
    bins low  = {0};
    bins high = {1};
  }
  out_cp : coverpoint sync_out {
    bins low  = {0};
    bins high = {1};
  }
  out_trans_cp : coverpoint sync_out {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
  }
  in_x_out : cross in_cp, out_cp;
endgroup""")
