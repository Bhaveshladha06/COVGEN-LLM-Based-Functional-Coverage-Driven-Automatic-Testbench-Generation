`timescale 1ns/1ps
module fsm_traffic_coverage (
  input logic clk,
  input logic rst_n,
  input logic sensor,
  input logic red,
  input logic yellow,
  input logic green
);

  // Local parameters for inferred states, matching DUT's internal states
  // S_RED = 2'd0, S_GREEN = 2'd1, S_YELLOW = 2'd2 from DUT's localparams.
  localparam S_RED = 2'd0;
  localparam S_GREEN = 2'd1;
  localparam S_YELLOW = 2'd2;
  // S_INVALID (2'd3) is used when the outputs (red, yellow, green) are not mutually exclusive
  // or when all are off, indicating an illegal state for the traffic light.
  localparam S_INVALID = 2'd3;

  // ALL declarations go at the TOP of a begin...end block, before any statement.
  // These are module-level declarations.
  logic [1:0] current_state_inferred;
  logic [1:0] prev_state_inferred;

  // Infer the current state from the DUT's output ports.
  // This assignment is continuous and not within a begin...end block.
  assign current_state_inferred = red ? S_RED : (green ? S_GREEN : (yellow ? S_YELLOW : S_INVALID));

  // Capture the previous state on the positive edge of the clock.
  always @(posedge clk) begin
    // No declarations needed inside this begin...end block.
    prev_state_inferred <= current_state_inferred;
  end

  covergroup fsm_traffic_coverage_cg @(posedge clk);
    option.per_instance = 1;

    // Requirement: "Cover every state of the traffic light controller: red, green and yellow."
    // Bin boundaries derived from RTL: S_RED (2'd0), S_GREEN (2'd1), S_YELLOW (2'd2).
    // S_INVALID (2'd3) is an illegal state, covering the mutual exclusivity requirement.
    state_cp : coverpoint current_state_inferred {
      bins red_s    = {S_RED};
      bins green_s  = {S_GREEN};
      bins yellow_s = {S_YELLOW};
      // Requirement: "Confirm the three output lights are mutually exclusive: exactly one is on at any time."
      // If current_state_inferred is S_INVALID (2'd3), it means the outputs are not mutually exclusive.
      illegal_bins invalid_state = {S_INVALID};
    }

    // Requirement: "Cover the sensor asserted and deasserted in each state." (partially covered here)
    // This coverpoint captures the sensor's value.
    sensor_cp : coverpoint sensor {
      bins sensor_off = {0};
      bins sensor_on  = {1};
    }

    // Requirement: "Cover the red state being held because the sensor is inactive even though the timer has expired"
    // In the RTL, if `state == S_RED` and `sensor == 0`, the state will always hold,
    // regardless of the timer value. The `iff (sensor == 0)` condition captures this.
    // This coverpoint contains transition bins and must not appear in a cross.
    red_hold_sensor_inactive_cp : coverpoint current_state_inferred iff (sensor == 0) {
      bins hold_red_sensor_off = (S_RED => S_RED);
    }

    // Requirement: "and cover it being held because the timer has not yet expired."
    // In the RTL, if `state == S_RED` and `sensor == 1`, but the state holds,
    // it implies `timer < 4'd5`. The `iff (sensor == 1)` condition captures this.
    // This coverpoint contains transition bins and must not appear in a cross.
    red_hold_timer_not_expired_cp : coverpoint current_state_inferred iff (sensor == 1) {
      bins hold_red_timer_not_exp = (S_RED => S_RED);
    }

    // Requirement: "Cover every legal transition between them: red to green"
    // In the RTL, this transition occurs when `state == S_RED`, `sensor == 1`, and `timer >= 4'd5`.
    // The `iff (sensor == 1)` captures the observable condition for this transition.
    // This coverpoint contains transition bins and must not appear in a cross.
    red_to_green_cp : coverpoint current_state_inferred iff (sensor == 1) {
      bins red_to_green = (S_RED => S_GREEN);
    }

    // Requirement: "Cover every legal transition between them: green to yellow"
    // In the RTL, this transition occurs when `state == S_GREEN` and `timer >= 4'd8`.
    // There is no `sensor` condition for this transition.
    // This coverpoint contains transition bins and must not appear in a cross.
    green_to_yellow_cp : coverpoint current_state_inferred {
      bins green_to_yellow = (S_GREEN => S_YELLOW);
    }

    // Requirement: "Cover every legal transition between them: yellow back to red"
    // In the RTL, this transition occurs when `state == S_YELLOW` and `timer >= 4'd2`.
    // There is no `sensor` condition for this transition.
    // This coverpoint contains transition bins and must not appear in a cross.
    yellow_to_red_cp : coverpoint current_state_inferred {
      bins yellow_to_red = (S_YELLOW => S_RED);
    }

    // Requirement: "Cover the sensor asserted and deasserted in each state."
    // This cross combines the state and sensor coverpoints.
    // Pruning: The 'invalid_state' bin from state_cp is automatically excluded from the cross.
    state_x_sensor_x : cross state_cp, sensor_cp;

  endgroup

  fsm_traffic_coverage_cg cg_inst = new();

  // Report the covergroup score directly from the simulator, so the
  // number does not depend on the coverage database or IMC's flags.
  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
  end

endmodule