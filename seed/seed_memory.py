"""Memory and storage seed designs for the coverage knowledge base."""

E = []


def add(eid, dtype, width, module, signals, req, rtl, cg):
    E.append(dict(id=eid, design_context=dict(module=module, data_width=width, type=dtype),
                  signals=signals, english_requirement=req, rtl=rtl, coverage_model=cg))


add("fifo_sync_8bit_001", "synchronous FIFO", 8, "FIFO_SYNC",
    ["clk", "rst_n", "wr_en", "rd_en", "din", "dout", "full", "empty"],
    "Cover the synchronous FIFO going both full and empty, simultaneous read and write while partially filled, write attempts while full and read attempts while empty being rejected, and the cross of write against read enables.",
    """module fifo_sync(clk, rst_n, wr_en, rd_en, din, dout, full, empty);
  input clk, rst_n, wr_en, rd_en;
  input [7:0] din;
  output reg [7:0] dout;
  output full, empty;
  reg [7:0] mem [0:7];
  reg [3:0] cnt;
  reg [2:0] wptr, rptr;
  assign full  = (cnt == 4'd8);
  assign empty = (cnt == 4'd0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cnt <= 0; wptr <= 0; rptr <= 0;
    end else begin
      if (wr_en && !full)  begin mem[wptr] <= din; wptr <= wptr + 1'b1; end
      if (rd_en && !empty) begin dout <= mem[rptr]; rptr <= rptr + 1'b1; end
      case ({wr_en && !full, rd_en && !empty})
        2'b10: cnt <= cnt + 1'b1;
        2'b01: cnt <= cnt - 1'b1;
        default: cnt <= cnt;
      endcase
    end
  end
endmodule""",
    """covergroup cg_fifo (ref logic [3:0] cnt, ref logic wr_en, rd_en, full, empty) @(posedge clk);
  cnt_cp : coverpoint cnt {
    bins empty_c   = {0};
    bins almost_e  = {1};
    bins mid       = {[2:6]};
    bins almost_f  = {7};
    bins full_c    = {8};
    illegal_bins overflow = {[9:15]};
  }
  wr_cp : coverpoint wr_en {
    bins idle  = {0};
    bins write = {1};
  }
  rd_cp : coverpoint rd_en {
    bins idle = {0};
    bins read = {1};
  }
  full_cp : coverpoint full {
    bins not_full = {0};
    bins is_full  = {1};
  }
  empty_cp : coverpoint empty {
    bins not_empty = {0};
    bins is_empty  = {1};
  }
  cnt_trans_cp : coverpoint cnt {
    bins fill_up   = (7 => 8);
    bins drain_out = (1 => 0);
  }
  wr_x_rd    : cross wr_cp, rd_cp;
  wr_x_full  : cross wr_cp, full_cp;
  rd_x_empty : cross rd_cp, empty_cp;
endgroup""")

add("lifo_stack_8bit_001", "LIFO stack", 8, "LIFO_STACK",
    ["clk", "rst_n", "push", "pop", "din", "dout", "full", "empty"],
    "Cover the stack pushing until full, popping until empty, push attempts while full and pop attempts while empty being ignored, and the cross of push against pop.",
    """module lifo_stack(clk, rst_n, push, pop, din, dout, full, empty);
  input clk, rst_n, push, pop;
  input [7:0] din;
  output [7:0] dout;
  output full, empty;
  reg [7:0] mem [0:7];
  reg [3:0] sp;
  assign full  = (sp == 4'd8);
  assign empty = (sp == 4'd0);
  assign dout  = empty ? 8'b0 : mem[sp - 1'b1];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) sp <= 0;
    else if (push && !full) begin mem[sp] <= din; sp <= sp + 1'b1; end
    else if (pop && !empty) sp <= sp - 1'b1;
  end
endmodule""",
    """covergroup cg_stack (ref logic [3:0] sp, ref logic push, pop, full, empty) @(posedge clk);
  sp_cp : coverpoint sp {
    bins empty_s = {0};
    bins mid     = {[1:7]};
    bins full_s  = {8};
    illegal_bins overflow = {[9:15]};
  }
  push_cp : coverpoint push {
    bins idle = {0};
    bins push = {1};
  }
  pop_cp : coverpoint pop {
    bins idle = {0};
    bins pop  = {1};
  }
  full_cp : coverpoint full {
    bins not_full = {0};
    bins is_full  = {1};
  }
  empty_cp : coverpoint empty {
    bins not_empty = {0};
    bins is_empty  = {1};
  }
  push_x_pop   : cross push_cp, pop_cp;
  push_x_full  : cross push_cp, full_cp;
  pop_x_empty  : cross pop_cp, empty_cp;
endgroup""")

add("ram_sp_8bit_001", "single-port RAM", 8, "RAM_SP",
    ["clk", "we", "addr", "din", "dout"],
    "Cover the single-port RAM writing and reading across the low, middle, and high address ranges, the boundary addresses, and the cross of write enable against address range.",
    """module ram_sp(clk, we, addr, din, dout);
  input clk, we;
  input [3:0] addr;
  input [7:0] din;
  output reg [7:0] dout;
  reg [7:0] mem [0:15];
  always @(posedge clk) begin
    if (we) mem[addr] <= din;
    dout <= mem[addr];
  end
endmodule""",
    """covergroup cg_ram_sp (ref logic [3:0] addr, ref logic [7:0] din, dout, ref logic we) @(posedge clk);
  addr_cp : coverpoint addr {
    bins first = {0};
    bins low   = {[1:7]};
    bins high  = {[8:14]};
    bins last  = {15};
  }
  we_cp : coverpoint we {
    bins read  = {0};
    bins write = {1};
  }
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  addr_x_we : cross addr_cp, we_cp;
endgroup""")

add("ram_dp_8bit_001", "dual-port RAM", 8, "RAM_DP",
    ["clk", "we_a", "addr_a", "din_a", "dout_a", "addr_b", "dout_b"],
    "Cover the dual-port RAM writing on port A while reading on port B, both ports addressing the same location simultaneously, and address coverage across the full range on both ports.",
    """module ram_dp(clk, we_a, addr_a, din_a, dout_a, addr_b, dout_b);
  input clk, we_a;
  input [3:0] addr_a, addr_b;
  input [7:0] din_a;
  output reg [7:0] dout_a, dout_b;
  reg [7:0] mem [0:15];
  always @(posedge clk) begin
    if (we_a) mem[addr_a] <= din_a;
    dout_a <= mem[addr_a];
    dout_b <= mem[addr_b];
  end
endmodule""",
    """covergroup cg_ram_dp (ref logic [3:0] addr_a, addr_b, ref logic we_a) @(posedge clk);
  addr_a_cp : coverpoint addr_a {
    bins low  = {[0:7]};
    bins high = {[8:15]};
  }
  addr_b_cp : coverpoint addr_b {
    bins low  = {[0:7]};
    bins high = {[8:15]};
  }
  we_cp : coverpoint we_a {
    bins idle  = {0};
    bins write = {1};
  }
  addr_a_x_b  : cross addr_a_cp, addr_b_cp;
  we_x_addr_a : cross we_cp, addr_a_cp;
endgroup""")

add("rom8_8bit_001", "8-entry ROM", 8, "ROM8", ["addr", "dout"],
    "Cover the ROM being read at every address including the first and last entries, and confirm the returned data spans the zero, mid-range, and maximum stored values.",
    """module rom8(addr, dout);
  input [2:0] addr;
  output reg [7:0] dout;
  always @(*) begin
    case (addr)
      3'd0: dout = 8'h00;
      3'd1: dout = 8'h11;
      3'd2: dout = 8'h22;
      3'd3: dout = 8'h33;
      3'd4: dout = 8'h44;
      3'd5: dout = 8'h55;
      3'd6: dout = 8'h66;
      3'd7: dout = 8'hFF;
    endcase
  end
endmodule""",
    """covergroup cg_rom8 (ref logic [2:0] addr, ref logic [7:0] dout);
  addr_cp : coverpoint addr {
    bins entry[] = {[0:7]};
  }
  dout_cp : coverpoint dout {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  addr_x_dout : cross addr_cp, dout_cp;
endgroup""")

add("regfile_8bit_001", "register file", 8, "REGFILE",
    ["clk", "rst_n", "we", "waddr", "wdata", "raddr1", "rdata1", "raddr2", "rdata2"],
    "Cover the register file writing to every register, reading from both read ports across the full address range, the read-during-write hazard where a read address matches the write address, and register zero being addressed.",
    """module regfile(clk, rst_n, we, waddr, wdata, raddr1, rdata1, raddr2, rdata2);
  input clk, rst_n, we;
  input [2:0] waddr, raddr1, raddr2;
  input [7:0] wdata;
  output [7:0] rdata1, rdata2;
  reg [7:0] regs [0:7];
  integer i;
  assign rdata1 = regs[raddr1];
  assign rdata2 = regs[raddr2];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) for (i = 0; i < 8; i = i + 1) regs[i] <= 8'b0;
    else if (we) regs[waddr] <= wdata;
  end
endmodule""",
    """covergroup cg_regfile (ref logic [2:0] waddr, raddr1, raddr2, ref logic we) @(posedge clk);
  waddr_cp : coverpoint waddr {
    bins reg_zero = {0};
    bins others[] = {[1:7]};
  }
  raddr1_cp : coverpoint raddr1 {
    bins reg_zero = {0};
    bins others[] = {[1:7]};
  }
  raddr2_cp : coverpoint raddr2 {
    bins reg_zero = {0};
    bins others[] = {[1:7]};
  }
  we_cp : coverpoint we {
    bins idle  = {0};
    bins write = {1};
  }
  we_x_waddr    : cross we_cp, waddr_cp;
  waddr_x_raddr1: cross waddr_cp, raddr1_cp;
endgroup""")

add("cam4_8bit_001", "content addressable memory", 8, "CAM4",
    ["clk", "rst_n", "we", "waddr", "wdata", "search", "match", "match_addr"],
    "Cover the CAM reporting a match when the searched value is present and no match when absent, matches at the first and last entries, and writes to every entry.",
    """module cam4(clk, rst_n, we, waddr, wdata, search, match, match_addr);
  input clk, rst_n, we;
  input [1:0] waddr;
  input [7:0] wdata, search;
  output match;
  output reg [1:0] match_addr;
  reg [7:0] mem [0:3];
  wire [3:0] hit;
  assign hit[0] = (mem[0] == search);
  assign hit[1] = (mem[1] == search);
  assign hit[2] = (mem[2] == search);
  assign hit[3] = (mem[3] == search);
  assign match = |hit;
  always @(*) begin
    casex (hit)
      4'bxxx1: match_addr = 2'd0;
      4'bxx10: match_addr = 2'd1;
      4'bx100: match_addr = 2'd2;
      4'b1000: match_addr = 2'd3;
      default: match_addr = 2'd0;
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mem[0] <= 0; mem[1] <= 0; mem[2] <= 0; mem[3] <= 0;
    end else if (we) mem[waddr] <= wdata;
  end
endmodule""",
    """covergroup cg_cam4 (ref logic [1:0] waddr, match_addr, ref logic we, match) @(posedge clk);
  waddr_cp : coverpoint waddr {
    bins entry[] = {[0:3]};
  }
  match_cp : coverpoint match {
    bins miss = {0};
    bins hit  = {1};
  }
  match_addr_cp : coverpoint match_addr {
    bins entry[] = {[0:3]};
  }
  we_cp : coverpoint we {
    bins idle  = {0};
    bins write = {1};
  }
  match_x_addr : cross match_cp, match_addr_cp;
  we_x_waddr   : cross we_cp, waddr_cp;
endgroup""")

add("circular_buffer_8bit_001", "circular buffer", 8, "CIRCULAR_BUFFER",
    ["clk", "rst_n", "wr_en", "rd_en", "din", "dout", "count"],
    "Cover the circular buffer wrapping its write and read pointers past the end of storage, the occupancy count spanning empty through full, and simultaneous read and write.",
    """module circular_buffer(clk, rst_n, wr_en, rd_en, din, dout, count);
  input clk, rst_n, wr_en, rd_en;
  input [7:0] din;
  output reg [7:0] dout;
  output reg [2:0] count;
  reg [7:0] mem [0:3];
  reg [1:0] wptr, rptr;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr <= 0; rptr <= 0; count <= 0;
    end else begin
      if (wr_en && count < 4) begin mem[wptr] <= din; wptr <= wptr + 1'b1; end
      if (rd_en && count > 0) begin dout <= mem[rptr]; rptr <= rptr + 1'b1; end
      case ({wr_en && count < 4, rd_en && count > 0})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule""",
    """covergroup cg_circbuf (ref logic [2:0] count, ref logic [1:0] wptr, rptr, ref logic wr_en, rd_en) @(posedge clk);
  count_cp : coverpoint count {
    bins empty_c = {0};
    bins mid     = {[1:3]};
    bins full_c  = {4};
    illegal_bins overflow = {[5:7]};
  }
  wptr_cp : coverpoint wptr {
    bins p[] = {[0:3]};
  }
  wptr_trans_cp : coverpoint wptr {
    bins wrap = (3 => 0);
    bins step = (0 => 1);
  }
  wr_cp : coverpoint wr_en {
    bins idle  = {0};
    bins write = {1};
  }
  rd_cp : coverpoint rd_en {
    bins idle = {0};
    bins read = {1};
  }
  wr_x_rd    : cross wr_cp, rd_cp;
  count_x_wr : cross count_cp, wr_cp;
endgroup""")

add("shift_fifo_4bit_001", "shift-register FIFO", 4, "SHIFT_FIFO",
    ["clk", "rst_n", "push", "din", "dout", "valid"],
    "Cover the shift-register FIFO filling from empty to full, the valid flag asserting once data is present, and data propagating through every stage.",
    """module shift_fifo(clk, rst_n, push, din, dout, valid);
  input clk, rst_n, push;
  input [3:0] din;
  output [3:0] dout;
  output valid;
  reg [3:0] s0, s1, s2, s3;
  reg [2:0] fill;
  assign dout  = s3;
  assign valid = (fill != 3'd0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s0 <= 0; s1 <= 0; s2 <= 0; s3 <= 0; fill <= 0;
    end else if (push) begin
      s0 <= din; s1 <= s0; s2 <= s1; s3 <= s2;
      if (fill < 3'd4) fill <= fill + 1'b1;
    end
  end
endmodule""",
    """covergroup cg_shift_fifo (ref logic [2:0] fill, ref logic [3:0] din, dout, ref logic push, valid) @(posedge clk);
  fill_cp : coverpoint fill {
    bins empty_f = {0};
    bins partial = {[1:3]};
    bins full_f  = {4};
    illegal_bins overflow = {[5:7]};
  }
  push_cp : coverpoint push {
    bins idle = {0};
    bins push = {1};
  }
  valid_cp : coverpoint valid {
    bins no_data  = {0};
    bins has_data = {1};
  }
  din_cp : coverpoint din {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  fill_x_push  : cross fill_cp, push_cp;
  valid_x_push : cross valid_cp, push_cp;
endgroup""")

add("scratchpad_8bit_001", "byte-enabled scratchpad memory", 8, "SCRATCHPAD",
    ["clk", "we", "be", "addr", "din", "dout"],
    "Cover the byte-enabled scratchpad writing with each byte-enable pattern including none and all bytes enabled, across the address range, crossing byte enable against write enable.",
    """module scratchpad(clk, we, be, addr, din, dout);
  input clk, we;
  input [1:0] be;
  input [2:0] addr;
  input [15:0] din;
  output reg [15:0] dout;
  reg [15:0] mem [0:7];
  always @(posedge clk) begin
    if (we) begin
      if (be[0]) mem[addr][7:0]  <= din[7:0];
      if (be[1]) mem[addr][15:8] <= din[15:8];
    end
    dout <= mem[addr];
  end
endmodule""",
    """covergroup cg_scratchpad (ref logic [1:0] be, ref logic [2:0] addr, ref logic we) @(posedge clk);
  be_cp : coverpoint be {
    bins none      = {2'b00};
    bins lower     = {2'b01};
    bins upper     = {2'b10};
    bins both      = {2'b11};
  }
  addr_cp : coverpoint addr {
    bins first  = {0};
    bins mid    = {[1:6]};
    bins last   = {7};
  }
  we_cp : coverpoint we {
    bins read  = {0};
    bins write = {1};
  }
  be_x_we   : cross be_cp, we_cp;
  addr_x_we : cross addr_cp, we_cp;
endgroup""")

add("fifo_depth_track_001", "FIFO with watermark flags", 8, "FIFO_WATERMARK",
    ["clk", "rst_n", "wr_en", "rd_en", "count", "almost_full", "almost_empty"],
    "Cover the FIFO watermark flags asserting and deasserting as occupancy crosses the programmable thresholds, and the occupancy transitioning across each watermark boundary in both directions.",
    """module fifo_watermark(clk, rst_n, wr_en, rd_en, count, almost_full, almost_empty);
  input clk, rst_n, wr_en, rd_en;
  output reg [3:0] count;
  output almost_full, almost_empty;
  assign almost_full  = (count >= 4'd12);
  assign almost_empty = (count <= 4'd2);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) count <= 4'b0;
    else begin
      case ({wr_en && count < 15, rd_en && count > 0})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule""",
    """covergroup cg_fifo_wm (ref logic [3:0] count, ref logic wr_en, rd_en, almost_full, almost_empty) @(posedge clk);
  count_cp : coverpoint count {
    bins very_low  = {[0:2]};
    bins low       = {[3:7]};
    bins high      = {[8:11]};
    bins very_high = {[12:15]};
  }
  af_cp : coverpoint almost_full {
    bins clear = {0};
    bins set   = {1};
  }
  ae_cp : coverpoint almost_empty {
    bins clear = {0};
    bins set   = {1};
  }
  count_trans_cp : coverpoint count {
    bins cross_ae_up   = (2 => 3);
    bins cross_ae_down = (3 => 2);
    bins cross_af_up   = (11 => 12);
    bins cross_af_down = (12 => 11);
  }
  af_x_ae : cross af_cp, ae_cp;
endgroup""")

add("mailbox_8bit_001", "single-entry mailbox", 8, "MAILBOX",
    ["clk", "rst_n", "put", "get", "din", "dout", "occupied"],
    "Cover the mailbox accepting a message when empty, rejecting a put while occupied, delivering on get, and the occupied flag transitioning in both directions.",
    """module mailbox(clk, rst_n, put, get, din, dout, occupied);
  input clk, rst_n, put, get;
  input [7:0] din;
  output reg [7:0] dout;
  output reg occupied;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      occupied <= 1'b0;
      dout     <= 8'b0;
    end else if (put && !occupied) begin
      dout     <= din;
      occupied <= 1'b1;
    end else if (get && occupied) begin
      occupied <= 1'b0;
    end
  end
endmodule""",
    """covergroup cg_mailbox (ref logic put, get, occupied, ref logic [7:0] din) @(posedge clk);
  put_cp : coverpoint put {
    bins idle = {0};
    bins put  = {1};
  }
  get_cp : coverpoint get {
    bins idle = {0};
    bins get  = {1};
  }
  occ_cp : coverpoint occupied {
    bins empty_m    = {0};
    bins occupied_m = {1};
  }
  occ_trans_cp : coverpoint occupied {
    bins fill  = (0 => 1);
    bins drain = (1 => 0);
  }
  put_x_occ : cross put_cp, occ_cp;
  get_x_occ : cross get_cp, occ_cp;
  put_x_get : cross put_cp, get_cp;
endgroup""")
