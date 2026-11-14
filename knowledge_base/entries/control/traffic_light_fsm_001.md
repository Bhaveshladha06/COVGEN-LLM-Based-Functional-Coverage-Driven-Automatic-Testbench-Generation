---
id: "traffic_light_fsm_001"
context.module: "TRAFFIC_LIGHT"
context.data_width: 2
context.type: "traffic light FSM"
signals: ["clk", "rst_n", "timer_done", "state", "lights"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the traffic light FSM visiting every state, each legal state transition in sequence, the full cycle returning to the initial state, and holding in a state while the timer has not expired.

## Notes
(none)

## RTL
```verilog
module traffic_light(clk, rst_n, timer_done, state, lights);
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
endmodule
```

## Coverage model
```systemverilog
covergroup cg_traffic (ref logic [1:0] state, ref logic timer_done) @(posedge clk);
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
endgroup
```
