`timescale 1ns/1ps
// Deliberately INCOMPLETE stimulus. It counts to 5 and stops, so the bins for
// 8..14, for 15, and for the 15=>0 wrap can never be hit. That is the point:
// the reports should show exactly those as uncovered.
module tb_counter (
  input  logic       clk,
  input  logic [3:0] count,
  output logic       rst_n,
  output logic       en
);
  initial begin
    rst_n = 1'b0;   en = 1'b0;      // reset asserted, enable off
    repeat (3) @(posedge clk);
    rst_n = 1'b1;                   // reset released

    en = 1'b1;                      // count 0 -> 1 -> 2 -> 3 -> 4 -> 5
    repeat (5) @(posedge clk);

    en = 1'b0;                      // hold at 5
    repeat (4) @(posedge clk);

    $display("TB: finished with count = %0d", count);
    $finish;
  end
endmodule
