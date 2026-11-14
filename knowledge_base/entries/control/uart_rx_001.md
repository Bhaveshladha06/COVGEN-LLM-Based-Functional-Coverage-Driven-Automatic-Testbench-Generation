---
id: "uart_rx_001"
context.module: "UART_RX"
context.data_width: 8
context.type: "UART receiver"
signals: ["clk", "rst_n", "rx", "data", "valid", "state", "framing_err"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the UART receiver detecting the start bit, sampling every data bit position, validating the stop bit, asserting the received-data valid flag, and flagging a framing error on a bad stop bit.

## Notes
(none)

## RTL
```verilog
module uart_rx(clk, rst_n, rx, data, valid, state, framing_err);
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
endmodule
```

## Coverage model
```systemverilog
covergroup cg_uart_rx (ref logic [1:0] state, ref logic [2:0] bitpos, ref logic rx, valid, framing_err) @(posedge clk);
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
endgroup
```
