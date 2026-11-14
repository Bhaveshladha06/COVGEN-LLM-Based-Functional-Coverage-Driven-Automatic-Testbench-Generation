"""FSM, protocol, and datapath seed designs for the coverage knowledge base."""

E = []


def add(eid, dtype, width, module, signals, req, rtl, cg):
    E.append(dict(id=eid, design_context=dict(module=module, data_width=width, type=dtype),
                  signals=signals, english_requirement=req, rtl=rtl, coverage_model=cg))


add("traffic_light_fsm_001", "traffic light FSM", 2, "TRAFFIC_LIGHT",
    ["clk", "rst_n", "timer_done", "state", "lights"],
    "Cover the traffic light FSM visiting every state, each legal state transition in sequence, the full cycle returning to the initial state, and holding in a state while the timer has not expired.",
    """module traffic_light(clk, rst_n, timer_done, state, lights);
  input clk, rst_n, timer_done;
  output reg [1:0] state;
  output reg [2:0] lights;
  parameter RED = 2'd0, GREEN = 2'd1, YELLOW = 2'd2;
  always @(*) begin
    case (state)
      RED:    lights = 3'b100;
      GREEN:  lights = 3'b001;
      YELLOW: lights = 3'b010;
      default:lights = 3'b100;
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= RED;
    else if (timer_done) begin
      case (state)
        RED:    state <= GREEN;
        GREEN:  state <= YELLOW;
        YELLOW: state <= RED;
        default:state <= RED;
      endcase
    end
  end
endmodule""",
    """covergroup cg_traffic (ref logic [1:0] state, ref logic timer_done) @(posedge clk);
  state_cp : coverpoint state {
    bins red    = {2'd0};
    bins green  = {2'd1};
    bins yellow = {2'd2};
    illegal_bins unused = {2'd3};
  }
  timer_cp : coverpoint timer_done {
    bins waiting = {0};
    bins expired = {1};
  }
  state_trans_cp : coverpoint state {
    bins red_to_green    = (2'd0 => 2'd1);
    bins green_to_yellow = (2'd1 => 2'd2);
    bins yellow_to_red   = (2'd2 => 2'd0);
    bins hold_red        = (2'd0 => 2'd0);
    bins hold_green      = (2'd1 => 2'd1);
  }
  state_x_timer : cross state_cp, timer_cp;
endgroup""")

add("vending_fsm_001", "vending machine FSM", 2, "VENDING",
    ["clk", "rst_n", "coin", "total", "dispense", "change"],
    "Cover the vending machine accumulating each accepted coin value, reaching and exceeding the item price, dispensing the item, and returning change when overpaid.",
    """module vending(clk, rst_n, coin, total, dispense, change);
  input clk, rst_n;
  input [1:0] coin;
  output reg [3:0] total;
  output dispense, change;
  assign dispense = (total >= 4'd10);
  assign change   = (total > 4'd10);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)          total <= 4'd0;
    else if (dispense)   total <= 4'd0;
    else begin
      case (coin)
        2'd1: total <= total + 4'd1;
        2'd2: total <= total + 4'd5;
        default: total <= total;
      endcase
    end
  end
endmodule""",
    """covergroup cg_vending (ref logic [1:0] coin, ref logic [3:0] total, ref logic dispense, change) @(posedge clk);
  coin_cp : coverpoint coin {
    bins none    = {2'd0};
    bins nickel  = {2'd1};
    bins dime    = {2'd2};
    bins invalid = {2'd3};
  }
  total_cp : coverpoint total {
    bins empty_t  = {0};
    bins partial  = {[1:9]};
    bins exact    = {10};
    bins over     = {[11:15]};
  }
  dispense_cp : coverpoint dispense {
    bins waiting   = {0};
    bins dispensed = {1};
  }
  change_cp : coverpoint change {
    bins no_change = {0};
    bins change    = {1};
  }
  coin_x_total     : cross coin_cp, total_cp;
  dispense_x_change: cross dispense_cp, change_cp;
endgroup""")

add("seq_detect_moore_001", "sequence detector 1011 (Moore)", 3, "SEQ_DETECT_MOORE",
    ["clk", "rst_n", "din", "state", "detected"],
    "Cover the Moore sequence detector visiting every state, detecting the target pattern, the overlapping detection case, and returning to the idle state on a mismatching bit.",
    """module seq_detect_moore(clk, rst_n, din, state, detected);
  input clk, rst_n, din;
  output reg [2:0] state;
  output detected;
  parameter S0=3'd0, S1=3'd1, S10=3'd2, S101=3'd3, S1011=3'd4;
  assign detected = (state == S1011);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S0;
    else begin
      case (state)
        S0:    state <= din ? S1   : S0;
        S1:    state <= din ? S1   : S10;
        S10:   state <= din ? S101 : S0;
        S101:  state <= din ? S1011: S10;
        S1011: state <= din ? S1   : S10;
        default: state <= S0;
      endcase
    end
  end
endmodule""",
    """covergroup cg_seq_moore (ref logic [2:0] state, ref logic din, detected) @(posedge clk);
  state_cp : coverpoint state {
    bins s0    = {3'd0};
    bins s1    = {3'd1};
    bins s10   = {3'd2};
    bins s101  = {3'd3};
    bins s1011 = {3'd4};
    illegal_bins unused = {[3'd5:3'd7]};
  }
  din_cp : coverpoint din {
    bins zero = {0};
    bins one  = {1};
  }
  detected_cp : coverpoint detected {
    bins no_match = {0};
    bins match    = {1};
  }
  state_trans_cp : coverpoint state {
    bins to_match   = (3'd3 => 3'd4);
    bins overlap    = (3'd4 => 3'd1);
    bins restart    = (3'd2 => 3'd0);
  }
  state_x_din : cross state_cp, din_cp;
endgroup""")

add("seq_detect_mealy_001", "sequence detector 110 (Mealy)", 2, "SEQ_DETECT_MEALY",
    ["clk", "rst_n", "din", "state", "detected"],
    "Cover the Mealy sequence detector across all states, the detection output asserting combinationally on the final input bit, and each state transition taken for both input values.",
    """module seq_detect_mealy(clk, rst_n, din, state, detected);
  input clk, rst_n, din;
  output reg [1:0] state;
  output detected;
  parameter S0=2'd0, S1=2'd1, S11=2'd2;
  assign detected = (state == S11) && (din == 1'b0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S0;
    else begin
      case (state)
        S0:  state <= din ? S1  : S0;
        S1:  state <= din ? S11 : S0;
        S11: state <= din ? S11 : S0;
        default: state <= S0;
      endcase
    end
  end
endmodule""",
    """covergroup cg_seq_mealy (ref logic [1:0] state, ref logic din, detected) @(posedge clk);
  state_cp : coverpoint state {
    bins s0  = {2'd0};
    bins s1  = {2'd1};
    bins s11 = {2'd2};
    illegal_bins unused = {2'd3};
  }
  din_cp : coverpoint din {
    bins zero = {0};
    bins one  = {1};
  }
  detected_cp : coverpoint detected {
    bins no_match = {0};
    bins match    = {1};
  }
  state_trans_cp : coverpoint state {
    bins build1 = (2'd0 => 2'd1);
    bins build2 = (2'd1 => 2'd2);
    bins fire   = (2'd2 => 2'd0);
  }
  state_x_din : cross state_cp, din_cp;
endgroup""")

add("arbiter_fixed_4bit_001", "fixed priority arbiter", 4, "ARBITER_FIXED",
    ["clk", "rst_n", "req", "grant"],
    "Cover the fixed priority arbiter granting each requester, the no-request idle case, simultaneous requests resolving to the highest priority, and confirm the grant is always one-hot or zero.",
    """module arbiter_fixed(clk, rst_n, req, grant);
  input clk, rst_n;
  input [3:0] req;
  output reg [3:0] grant;
  always @(*) begin
    casex (req)
      4'bxxx1: grant = 4'b0001;
      4'bxx10: grant = 4'b0010;
      4'bx100: grant = 4'b0100;
      4'b1000: grant = 4'b1000;
      default: grant = 4'b0000;
    endcase
  end
endmodule""",
    """covergroup cg_arb_fixed (ref logic [3:0] req, grant);
  req_cp : coverpoint req {
    bins none      = {4'b0000};
    bins single[]  = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    bins multiple  = {[4'b0011:4'b0111], [4'b1001:4'b1111]};
  }
  grant_cp : coverpoint grant {
    bins idle     = {4'b0000};
    bins onehot[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    illegal_bins multi_grant = default;
  }
  req_x_grant : cross req_cp, grant_cp;
endgroup""")

add("arbiter_rr_4bit_001", "round-robin arbiter", 4, "ARBITER_RR",
    ["clk", "rst_n", "req", "grant", "last_grant"],
    "Cover the round-robin arbiter granting every requester in turn, rotating priority after each grant, handling simultaneous requests fairly, and the idle case with no requests.",
    """module arbiter_rr(clk, rst_n, req, grant, last_grant);
  input clk, rst_n;
  input [3:0] req;
  output reg [3:0] grant;
  output reg [1:0] last_grant;
  integer i;
  always @(*) begin
    grant = 4'b0000;
    for (i = 0; i < 4; i = i + 1) begin
      if (grant == 4'b0000 && req[(last_grant + 1 + i) % 4])
        grant[(last_grant + 1 + i) % 4] = 1'b1;
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) last_grant <= 2'd0;
    else if (grant != 4'b0000) begin
      case (grant)
        4'b0001: last_grant <= 2'd0;
        4'b0010: last_grant <= 2'd1;
        4'b0100: last_grant <= 2'd2;
        4'b1000: last_grant <= 2'd3;
        default: last_grant <= last_grant;
      endcase
    end
  end
endmodule""",
    """covergroup cg_arb_rr (ref logic [3:0] req, grant, ref logic [1:0] last_grant) @(posedge clk);
  req_cp : coverpoint req {
    bins none     = {4'b0000};
    bins single[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    bins all_req  = {4'b1111};
    bins multiple = {[4'b0011:4'b0111], [4'b1001:4'b1110]};
  }
  grant_cp : coverpoint grant {
    bins idle     = {4'b0000};
    bins onehot[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
  }
  last_cp : coverpoint last_grant {
    bins owner[] = {[0:3]};
  }
  last_trans_cp : coverpoint last_grant {
    bins rotate_0_1 = (2'd0 => 2'd1);
    bins rotate_1_2 = (2'd1 => 2'd2);
    bins rotate_2_3 = (2'd2 => 2'd3);
    bins rotate_3_0 = (2'd3 => 2'd0);
  }
  req_x_grant  : cross req_cp, grant_cp;
  last_x_grant : cross last_cp, grant_cp;
endgroup""")

add("handshake_vr_001", "valid-ready handshake", 8, "HANDSHAKE_VR",
    ["clk", "rst_n", "valid", "ready", "data", "xfer"],
    "Cover the valid-ready handshake for all four combinations of valid and ready, the transfer occurring only when both are asserted, valid waiting for ready, and back-to-back transfers.",
    """module handshake_vr(clk, rst_n, valid, ready, data, xfer);
  input clk, rst_n, valid, ready;
  input [7:0] data;
  output xfer;
  assign xfer = valid && ready;
endmodule""",
    """covergroup cg_handshake (ref logic valid, ready, xfer, ref logic [7:0] data) @(posedge clk);
  vr_cp : coverpoint {valid, ready} {
    bins idle        = {2'b00};
    bins ready_only  = {2'b01};
    bins valid_wait  = {2'b10};
    bins transfer    = {2'b11};
  }
  xfer_cp : coverpoint xfer {
    bins no_xfer = {0};
    bins xfer    = {1};
  }
  xfer_trans_cp : coverpoint xfer {
    bins back_to_back = (1 => 1);
    bins start        = (0 => 1);
    bins stop         = (1 => 0);
  }
  data_cp : coverpoint data {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  vr_x_data : cross vr_cp, data_cp;
endgroup""")

add("apb_slave_001", "APB slave interface", 8, "APB_SLAVE",
    ["clk", "rst_n", "psel", "penable", "pwrite", "paddr", "pwdata", "prdata", "pready"],
    "Cover the APB slave through its idle, setup, and access phases, both read and write transfers, the ready signal inserting wait states, and the address range covered on both transfer types.",
    """module apb_slave(clk, rst_n, psel, penable, pwrite, paddr, pwdata, prdata, pready);
  input clk, rst_n, psel, penable, pwrite;
  input [3:0] paddr;
  input [7:0] pwdata;
  output reg [7:0] prdata;
  output pready;
  reg [7:0] mem [0:15];
  assign pready = psel && penable;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) prdata <= 8'b0;
    else if (psel && penable) begin
      if (pwrite) mem[paddr] <= pwdata;
      else        prdata     <= mem[paddr];
    end
  end
endmodule""",
    """covergroup cg_apb (ref logic psel, penable, pwrite, pready, ref logic [3:0] paddr) @(posedge clk);
  phase_cp : coverpoint {psel, penable} {
    bins idle   = {2'b00};
    bins setup  = {2'b10};
    bins access = {2'b11};
    illegal_bins bad = {2'b01};
  }
  pwrite_cp : coverpoint pwrite {
    bins read  = {0};
    bins write = {1};
  }
  paddr_cp : coverpoint paddr {
    bins first = {0};
    bins mid   = {[1:14]};
    bins last  = {15};
  }
  pready_cp : coverpoint pready {
    bins wait_state = {0};
    bins ready      = {1};
  }
  phase_trans_cp : coverpoint {psel, penable} {
    bins idle_to_setup   = (2'b00 => 2'b10);
    bins setup_to_access = (2'b10 => 2'b11);
    bins access_to_idle  = (2'b11 => 2'b00);
  }
  phase_x_write : cross phase_cp, pwrite_cp;
  addr_x_write  : cross paddr_cp, pwrite_cp;
endgroup""")

add("uart_tx_001", "UART transmitter", 8, "UART_TX",
    ["clk", "rst_n", "start", "data", "tx", "busy", "state"],
    "Cover the UART transmitter through idle, start bit, all data bit positions, and stop bit states, transmitting both all-zero and all-one data payloads, and the busy flag across a full frame.",
    """module uart_tx(clk, rst_n, start, data, tx, busy, state);
  input clk, rst_n, start;
  input [7:0] data;
  output reg tx;
  output busy;
  output reg [1:0] state;
  reg [2:0] bitpos;
  reg [7:0] shifter;
  parameter IDLE=2'd0, START=2'd1, DATA=2'd2, STOP=2'd3;
  assign busy = (state != IDLE);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE; tx <= 1'b1; bitpos <= 3'd0;
    end else begin
      case (state)
        IDLE:  if (start) begin shifter <= data; tx <= 1'b0; state <= START; end
        START: begin tx <= shifter[0]; bitpos <= 3'd0; state <= DATA; end
        DATA:  begin
                 tx <= shifter[bitpos];
                 if (bitpos == 3'd7) state <= STOP;
                 else bitpos <= bitpos + 1'b1;
               end
        STOP:  begin tx <= 1'b1; state <= IDLE; end
      endcase
    end
  end
endmodule""",
    """covergroup cg_uart_tx (ref logic [1:0] state, ref logic [2:0] bitpos, ref logic [7:0] data, ref logic start, busy, tx) @(posedge clk);
  state_cp : coverpoint state {
    bins idle  = {2'd0};
    bins start = {2'd1};
    bins data  = {2'd2};
    bins stop  = {2'd3};
  }
  bitpos_cp : coverpoint bitpos {
    bins bit_n[] = {[0:7]};
  }
  data_cp : coverpoint data {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins mid      = {[8'h01:8'hFE]};
  }
  busy_cp : coverpoint busy {
    bins idle_b = {0};
    bins busy_b = {1};
  }
  state_trans_cp : coverpoint state {
    bins begin_frame = (2'd0 => 2'd1);
    bins send_data   = (2'd1 => 2'd2);
    bins finish      = (2'd2 => 2'd3);
    bins back_idle   = (2'd3 => 2'd0);
  }
  state_x_data : cross state_cp, data_cp;
endgroup""")

add("uart_rx_001", "UART receiver", 8, "UART_RX",
    ["clk", "rst_n", "rx", "data", "valid", "state", "framing_err"],
    "Cover the UART receiver detecting the start bit, sampling every data bit position, validating the stop bit, asserting the received-data valid flag, and flagging a framing error on a bad stop bit.",
    """module uart_rx(clk, rst_n, rx, data, valid, state, framing_err);
  input clk, rst_n, rx;
  output reg [7:0] data;
  output reg valid, framing_err;
  output reg [1:0] state;
  reg [2:0] bitpos;
  parameter IDLE=2'd0, START=2'd1, DATA=2'd2, STOP=2'd3;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE; valid <= 1'b0; framing_err <= 1'b0; bitpos <= 3'd0;
    end else begin
      valid <= 1'b0;
      case (state)
        IDLE:  if (!rx) state <= START;
        START: begin bitpos <= 3'd0; state <= DATA; end
        DATA:  begin
                 data[bitpos] <= rx;
                 if (bitpos == 3'd7) state <= STOP;
                 else bitpos <= bitpos + 1'b1;
               end
        STOP:  begin
                 framing_err <= ~rx;
                 valid       <= rx;
                 state       <= IDLE;
               end
      endcase
    end
  end
endmodule""",
    """covergroup cg_uart_rx (ref logic [1:0] state, ref logic [2:0] bitpos, ref logic rx, valid, framing_err) @(posedge clk);
  state_cp : coverpoint state {
    bins idle  = {2'd0};
    bins start = {2'd1};
    bins data  = {2'd2};
    bins stop  = {2'd3};
  }
  bitpos_cp : coverpoint bitpos {
    bins bit_n[] = {[0:7]};
  }
  valid_cp : coverpoint valid {
    bins no_data = {0};
    bins got_data= {1};
  }
  err_cp : coverpoint framing_err {
    bins ok    = {0};
    bins error = {1};
  }
  state_trans_cp : coverpoint state {
    bins detect_start = (2'd0 => 2'd1);
    bins receive      = (2'd1 => 2'd2);
    bins to_stop      = (2'd2 => 2'd3);
    bins complete     = (2'd3 => 2'd0);
  }
  valid_x_err : cross valid_cp, err_cp;
  state_x_rx  : cross state_cp, valid_cp;
endgroup""")

add("spi_master_001", "SPI master", 8, "SPI_MASTER",
    ["clk", "rst_n", "start", "mosi_data", "sclk", "mosi", "cs_n", "busy", "bitcnt"],
    "Cover the SPI master asserting and releasing chip select, shifting all eight bit positions, both clock phases within a transfer, and the busy flag spanning a complete transaction.",
    """module spi_master(clk, rst_n, start, mosi_data, sclk, mosi, cs_n, busy, bitcnt);
  input clk, rst_n, start;
  input [7:0] mosi_data;
  output reg sclk, mosi, cs_n, busy;
  output reg [3:0] bitcnt;
  reg [7:0] shifter;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cs_n <= 1'b1; busy <= 1'b0; bitcnt <= 4'd0; sclk <= 1'b0;
    end else if (!busy && start) begin
      shifter <= mosi_data; cs_n <= 1'b0; busy <= 1'b1; bitcnt <= 4'd0;
    end else if (busy) begin
      sclk <= ~sclk;
      if (sclk) begin
        mosi   <= shifter[7];
        shifter<= {shifter[6:0], 1'b0};
        if (bitcnt == 4'd7) begin busy <= 1'b0; cs_n <= 1'b1; end
        else bitcnt <= bitcnt + 1'b1;
      end
    end
  end
endmodule""",
    """covergroup cg_spi (ref logic [3:0] bitcnt, ref logic cs_n, busy, sclk, start) @(posedge clk);
  bitcnt_cp : coverpoint bitcnt {
    bins bit_n[] = {[0:7]};
    illegal_bins overflow = {[8:15]};
  }
  cs_cp : coverpoint cs_n {
    bins selected   = {0};
    bins deselected = {1};
  }
  busy_cp : coverpoint busy {
    bins idle = {0};
    bins busy = {1};
  }
  sclk_cp : coverpoint sclk {
    bins low  = {0};
    bins high = {1};
  }
  cs_trans_cp : coverpoint cs_n {
    bins assert_cs  = (1 => 0);
    bins release_cs = (0 => 1);
  }
  bitcnt_x_sclk : cross bitcnt_cp, sclk_cp;
  cs_x_busy     : cross cs_cp, busy_cp;
endgroup""")

add("i2c_cond_001", "I2C start/stop condition detector", 1, "I2C_COND",
    ["clk", "rst_n", "scl", "sda", "start_cond", "stop_cond"],
    "Cover the I2C condition detector recognising a start condition when data falls while clock is high, a stop condition when data rises while clock is high, and neither during normal data transitions.",
    """module i2c_cond(clk, rst_n, scl, sda, start_cond, stop_cond);
  input clk, rst_n, scl, sda;
  output start_cond, stop_cond;
  reg sda_d;
  assign start_cond = scl && sda_d && !sda;
  assign stop_cond  = scl && !sda_d && sda;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) sda_d <= 1'b1;
    else        sda_d <= sda;
  end
endmodule""",
    """covergroup cg_i2c_cond (ref logic scl, sda, start_cond, stop_cond) @(posedge clk);
  bus_cp : coverpoint {scl, sda} {
    bins both_low  = {2'b00};
    bins clk_low   = {2'b01};
    bins data_low  = {2'b10};
    bins both_high = {2'b11};
  }
  cond_cp : coverpoint {start_cond, stop_cond} {
    bins none  = {2'b00};
    bins stop  = {2'b01};
    bins start = {2'b10};
    illegal_bins both = {2'b11};
  }
  sda_trans_cp : coverpoint sda {
    bins fall = (1 => 0);
    bins rise = (0 => 1);
  }
  bus_x_cond : cross bus_cp, cond_cp;
endgroup""")

add("mult4_array_001", "4-bit array multiplier", 4, "MULT4",
    ["a", "b", "product"],
    "Cover the 4-bit array multiplier for zero, unity, and maximum operands, the full product range including the maximum product, and the cross of the two operand ranges.",
    """module mult4(a, b, product);
  input [3:0] a, b;
  output [7:0] product;
  assign product = a * b;
endmodule""",
    """covergroup cg_mult4 (ref logic [3:0] a, b, ref logic [7:0] product);
  a_cp : coverpoint a {
    bins zero = {0};
    bins one  = {1};
    bins mid  = {[2:14]};
    bins max  = {15};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins one  = {1};
    bins mid  = {[2:14]};
    bins max  = {15};
  }
  product_cp : coverpoint product {
    bins zero = {0};
    bins low  = {[1:63]};
    bins high = {[64:224]};
    bins max  = {225};
  }
  a_x_b : cross a_cp, b_cp;
endgroup""")

add("mult_seq_001", "sequential shift-add multiplier", 8, "MULT_SEQ",
    ["clk", "rst_n", "start", "a", "b", "product", "done", "bitcnt"],
    "Cover the sequential multiplier through every iteration of its shift-add loop, the start and done handshake, zero and maximum operands, and the multiplier bit determining whether an add occurs.",
    """module mult_seq(clk, rst_n, start, a, b, product, done, bitcnt);
  input clk, rst_n, start;
  input [3:0] a, b;
  output reg [7:0] product;
  output done;
  output reg [2:0] bitcnt;
  reg [3:0] mplier;
  reg running;
  assign done = !running && (bitcnt == 3'd4);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      product <= 8'b0; bitcnt <= 3'd0; running <= 1'b0;
    end else if (start && !running) begin
      product <= 8'b0; mplier <= b; bitcnt <= 3'd0; running <= 1'b1;
    end else if (running) begin
      if (mplier[0]) product <= product + (a << bitcnt);
      mplier <= mplier >> 1;
      if (bitcnt == 3'd3) running <= 1'b0;
      bitcnt <= bitcnt + 1'b1;
    end
  end
endmodule""",
    """covergroup cg_mult_seq (ref logic [2:0] bitcnt, ref logic [3:0] a, b, ref logic start, done, running) @(posedge clk);
  bitcnt_cp : coverpoint bitcnt {
    bins iter[] = {[0:4]};
    illegal_bins overflow = {[5:7]};
  }
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  running_cp : coverpoint running {
    bins idle    = {0};
    bins running = {1};
  }
  done_cp : coverpoint done {
    bins not_done = {0};
    bins done     = {1};
  }
  bitcnt_trans_cp : coverpoint bitcnt {
    bins step   = (0 => 1);
    bins finish = (3 => 4);
  }
  bitcnt_x_running : cross bitcnt_cp, running_cp;
  a_x_done         : cross a_cp, done_cp;
endgroup""")

add("divider_seq_001", "sequential restoring divider", 8, "DIVIDER_SEQ",
    ["clk", "rst_n", "start", "dividend", "divisor", "quotient", "remainder", "done", "div_zero"],
    "Cover the sequential divider producing quotients across the value range, a zero remainder for exact division, the divide-by-zero error flag, and the done handshake completing each operation.",
    """module divider_seq(clk, rst_n, start, dividend, divisor, quotient, remainder, done, div_zero);
  input clk, rst_n, start;
  input [7:0] dividend, divisor;
  output reg [7:0] quotient, remainder;
  output reg done;
  output div_zero;
  reg [3:0] cnt;
  reg running;
  assign div_zero = (divisor == 8'b0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      quotient <= 0; remainder <= 0; done <= 0; cnt <= 0; running <= 0;
    end else if (start && !running && !div_zero) begin
      quotient <= dividend / divisor;
      remainder<= dividend % divisor;
      running  <= 1'b1; cnt <= 4'd0; done <= 1'b0;
    end else if (running) begin
      if (cnt == 4'd7) begin running <= 1'b0; done <= 1'b1; end
      else cnt <= cnt + 1'b1;
    end else done <= 1'b0;
  end
endmodule""",
    """covergroup cg_divider (ref logic [7:0] dividend, divisor, quotient, remainder, ref logic done, div_zero) @(posedge clk);
  divisor_cp : coverpoint divisor {
    bins zero = {0};
    bins one  = {1};
    bins mid  = {[2:254]};
    bins max  = {255};
  }
  dividend_cp : coverpoint dividend {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  remainder_cp : coverpoint remainder {
    bins exact     = {0};
    bins non_exact = {[1:255]};
  }
  div_zero_cp : coverpoint div_zero {
    bins ok    = {0};
    bins error = {1};
  }
  done_cp : coverpoint done {
    bins busy = {0};
    bins done = {1};
  }
  divisor_x_rem : cross divisor_cp, remainder_cp;
  dividend_x_divisor : cross dividend_cp, divisor_cp;
endgroup""")

add("mac_unit_001", "multiply-accumulate unit", 8, "MAC_UNIT",
    ["clk", "rst_n", "en", "clear", "a", "b", "acc", "ovf"],
    "Cover the multiply-accumulate unit accumulating products across operand ranges, the clear operation resetting the accumulator, holding when disabled, and the overflow flag asserting.",
    """module mac_unit(clk, rst_n, en, clear, a, b, acc, ovf);
  input clk, rst_n, en, clear;
  input [3:0] a, b;
  output reg [15:0] acc;
  output reg ovf;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc <= 16'b0; ovf <= 1'b0;
    end else if (clear) begin
      acc <= 16'b0; ovf <= 1'b0;
    end else if (en) begin
      {ovf, acc} <= acc + (a * b);
    end
  end
endmodule""",
    """covergroup cg_mac (ref logic [3:0] a, b, ref logic [15:0] acc, ref logic en, clear, ovf) @(posedge clk);
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
  en_cp : coverpoint en {
    bins hold  = {0};
    bins accum = {1};
  }
  clear_cp : coverpoint clear {
    bins run   = {0};
    bins clear = {1};
  }
  ovf_cp : coverpoint ovf {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  a_x_b       : cross a_cp, b_cp;
  en_x_clear  : cross en_cp, clear_cp;
endgroup""")

add("crc8_001", "CRC-8 generator", 8, "CRC8",
    ["clk", "rst_n", "en", "din", "crc"],
    "Cover the CRC-8 generator processing both input bit values, the CRC register spanning its value range, the initial value after reset, and the feedback path being exercised in both states.",
    """module crc8(clk, rst_n, en, din, crc);
  input clk, rst_n, en, din;
  output reg [7:0] crc;
  wire fb = crc[7] ^ din;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  crc <= 8'h00;
    else if (en) crc <= {crc[6:0], 1'b0} ^ (fb ? 8'h07 : 8'h00);
  end
endmodule""",
    """covergroup cg_crc8 (ref logic [7:0] crc, ref logic din, en, fb) @(posedge clk);
  crc_cp : coverpoint crc {
    bins init = {8'h00};
    bins low  = {[8'h01:8'h7F]};
    bins high = {[8'h80:8'hFF]};
  }
  din_cp : coverpoint din {
    bins zero = {0};
    bins one  = {1};
  }
  fb_cp : coverpoint fb {
    bins no_xor = {0};
    bins do_xor = {1};
  }
  en_cp : coverpoint en {
    bins hold    = {0};
    bins process = {1};
  }
  din_x_fb : cross din_cp, fb_cp;
  crc_x_en : cross crc_cp, en_cp;
endgroup""")

add("fir_tap_001", "FIR filter tap", 8, "FIR_TAP",
    ["clk", "rst_n", "en", "din", "coeff", "dout"],
    "Cover the FIR filter tap for zero, positive, and maximum sample and coefficient values, the delay line propagating samples, and the accumulated output range.",
    """module fir_tap(clk, rst_n, en, din, coeff, dout);
  input clk, rst_n, en;
  input [7:0] din, coeff;
  output reg [15:0] dout;
  reg [7:0] delay;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      delay <= 8'b0; dout <= 16'b0;
    end else if (en) begin
      delay <= din;
      dout  <= delay * coeff;
    end
  end
endmodule""",
    """covergroup cg_fir (ref logic [7:0] din, coeff, delay, ref logic [15:0] dout, ref logic en) @(posedge clk);
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  coeff_cp : coverpoint coeff {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  en_cp : coverpoint en {
    bins hold   = {0};
    bins filter = {1};
  }
  dout_cp : coverpoint dout {
    bins zero = {16'h0000};
    bins mid  = {[16'h0001:16'hFE00]};
    bins high = {[16'hFE01:16'hFFFF]};
  }
  din_x_coeff : cross din_cp, coeff_cp;
endgroup""")

add("watchdog_timer_001", "watchdog timer", 8, "WATCHDOG",
    ["clk", "rst_n", "kick", "timeout", "counter"],
    "Cover the watchdog timer counting up towards its limit, being kicked before expiry to reload the counter, expiring and asserting the timeout, and the counter spanning its range.",
    """module watchdog(clk, rst_n, kick, timeout, counter);
  input clk, rst_n, kick;
  output timeout;
  output reg [7:0] counter;
  assign timeout = (counter == 8'hFF);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)        counter <= 8'b0;
    else if (kick)     counter <= 8'b0;
    else if (!timeout) counter <= counter + 1'b1;
  end
endmodule""",
    """covergroup cg_watchdog (ref logic [7:0] counter, ref logic kick, timeout) @(posedge clk);
  counter_cp : coverpoint counter {
    bins reloaded = {8'h00};
    bins early    = {[8'h01:8'h7F]};
    bins late     = {[8'h80:8'hFE]};
    bins expired  = {8'hFF};
  }
  kick_cp : coverpoint kick {
    bins idle = {0};
    bins kick = {1};
  }
  timeout_cp : coverpoint timeout {
    bins running = {0};
    bins expired = {1};
  }
  counter_trans_cp : coverpoint counter {
    bins reload_from_late = (8'h80 => 8'h00);
    bins reach_limit      = (8'hFE => 8'hFF);
  }
  kick_x_counter : cross kick_cp, counter_cp;
  kick_x_timeout : cross kick_cp, timeout_cp;
endgroup""")

add("pwm_001", "PWM generator", 8, "PWM",
    ["clk", "rst_n", "en", "duty", "pwm_out", "counter"],
    "Cover the PWM generator at zero, partial, and full duty-cycle settings, the output asserted and deasserted within a period, the counter wrapping at the end of each period, and holding while disabled.",
    """module pwm(clk, rst_n, en, duty, pwm_out, counter);
  input clk, rst_n, en;
  input [7:0] duty;
  output pwm_out;
  output reg [7:0] counter;
  assign pwm_out = en && (counter < duty);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  counter <= 8'b0;
    else if (en) counter <= counter + 1'b1;
  end
endmodule""",
    """covergroup cg_pwm (ref logic [7:0] duty, counter, ref logic en, pwm_out) @(posedge clk);
  duty_cp : coverpoint duty {
    bins always_off = {8'h00};
    bins low        = {[8'h01:8'h7F]};
    bins high       = {[8'h80:8'hFE]};
    bins always_on  = {8'hFF};
  }
  counter_cp : coverpoint counter {
    bins start = {8'h00};
    bins mid   = {[8'h01:8'hFE]};
    bins end_p = {8'hFF};
  }
  out_cp : coverpoint pwm_out {
    bins low  = {0};
    bins high = {1};
  }
  counter_trans_cp : coverpoint counter {
    bins period_wrap = (8'hFF => 8'h00);
  }
  duty_x_out : cross duty_cp, out_cp;
  en_x_out   : cross out_cp, duty_cp;
endgroup""")

add("intr_ctrl_001", "interrupt controller", 4, "INTR_CTRL",
    ["clk", "rst_n", "irq_in", "mask", "irq_out", "pending"],
    "Cover the interrupt controller with each interrupt source asserted, masked and unmasked, multiple simultaneous interrupts, and the aggregated output asserting only when an unmasked source is pending.",
    """module intr_ctrl(clk, rst_n, irq_in, mask, irq_out, pending);
  input clk, rst_n;
  input [3:0] irq_in, mask;
  output irq_out;
  output reg [3:0] pending;
  assign irq_out = |(pending & ~mask);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) pending <= 4'b0;
    else        pending <= pending | irq_in;
  end
endmodule""",
    """covergroup cg_intr (ref logic [3:0] irq_in, mask, pending, ref logic irq_out) @(posedge clk);
  irq_cp : coverpoint irq_in {
    bins none     = {4'b0000};
    bins single[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    bins multiple = {[4'b0011:4'b0111], [4'b1001:4'b1111]};
  }
  mask_cp : coverpoint mask {
    bins none_masked = {4'b0000};
    bins all_masked  = {4'b1111};
    bins partial     = {[4'b0001:4'b1110]};
  }
  out_cp : coverpoint irq_out {
    bins quiet     = {0};
    bins asserting = {1};
  }
  irq_x_mask : cross irq_cp, mask_cp;
  mask_x_out : cross mask_cp, out_cp;
endgroup""")

add("timer_compare_001", "timer with compare match", 8, "TIMER_COMPARE",
    ["clk", "rst_n", "en", "compare", "counter", "match"],
    "Cover the compare timer counting to the compare value, asserting the match output, restarting from zero after a match, compare values at the extremes, and holding while disabled.",
    """module timer_compare(clk, rst_n, en, compare, counter, match);
  input clk, rst_n, en;
  input [7:0] compare;
  output reg [7:0] counter;
  output match;
  assign match = (counter == compare);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)      counter <= 8'b0;
    else if (en)     counter <= match ? 8'b0 : (counter + 1'b1);
  end
endmodule""",
    """covergroup cg_timer_cmp (ref logic [7:0] compare, counter, ref logic en, match) @(posedge clk);
  compare_cp : coverpoint compare {
    bins immediate = {8'h00};
    bins short     = {[8'h01:8'h7F]};
    bins long      = {[8'h80:8'hFE]};
    bins max       = {8'hFF};
  }
  counter_cp : coverpoint counter {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  match_cp : coverpoint match {
    bins no_match = {0};
    bins matched  = {1};
  }
  en_cp : coverpoint en {
    bins stopped = {0};
    bins running = {1};
  }
  compare_x_match : cross compare_cp, match_cp;
  en_x_counter    : cross en_cp, counter_cp;
endgroup""")

add("clock_gate_001", "glitch-free clock gate", 1, "CLOCK_GATE",
    ["clk", "rst_n", "enable", "gated_clk", "latched_en"],
    "Cover the clock gate enabling and disabling the gated output, the enable being latched on the correct clock phase, and both transition directions of the latched enable.",
    """module clock_gate(clk, rst_n, enable, gated_clk, latched_en);
  input clk, rst_n, enable;
  output gated_clk;
  output reg latched_en;
  assign gated_clk = clk & latched_en;
  always @(negedge clk or negedge rst_n) begin
    if (!rst_n) latched_en <= 1'b0;
    else        latched_en <= enable;
  end
endmodule""",
    """covergroup cg_clkgate (ref logic enable, latched_en) @(posedge clk);
  enable_cp : coverpoint enable {
    bins off = {0};
    bins on  = {1};
  }
  latched_cp : coverpoint latched_en {
    bins gated   = {0};
    bins passing = {1};
  }
  latched_trans_cp : coverpoint latched_en {
    bins turn_on  = (0 => 1);
    bins turn_off = (1 => 0);
    bins stay_off = (0 => 0);
    bins stay_on  = (1 => 1);
  }
  enable_x_latched : cross enable_cp, latched_cp;
endgroup""")
