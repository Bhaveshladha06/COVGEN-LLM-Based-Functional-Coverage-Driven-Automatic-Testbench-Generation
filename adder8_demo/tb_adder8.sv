`timescale 1ns/1ps
// Testbench in exactly the shape the pipeline produces:
//   - a plain module with PORTS (no virtual interface -- *E,VIFCVU on irun 15.20)
//   - directions MIRRORED relative to the DUT: it drives a, b, cin and reads sum, cout
//   - all variables declared at module scope, before the initial blocks
//   - a watchdog so a broken run can never hang the server
//   - NO coverage code of any kind: it drives, the coverage module measures
//
// Combinational DUT, so vectors are separated by #10 rather than a clock edge.
//
// DELIBERATE HOLE: this never drives a=255 and b=255 at the same time, so the
// cross bin <max,max> stays empty. That is there so the detail report has
// something real to show you.
module tb_adder8 (
  input  logic [7:0] sum,
  input  logic       cout,
  output logic [7:0] a,
  output logic [7:0] b,
  output logic       cin
);

  integer i;

  // Watchdog: never let the simulation hang.
  initial begin
    #200000;
    $display("TB: watchdog timeout");
    $finish;
  end

  initial begin
    a = 8'd0; b = 8'd0; cin = 1'b0;
    #10;

    // ---- random phase --------------------------------------------------
    for (i = 0; i < 300; i = i + 1) begin
      a   = $urandom_range(0, 255);
      b   = $urandom_range(0, 255);
      cin = $urandom_range(0, 1);
      #10;
    end

    // ---- directed corners ----------------------------------------------
    a = 8'd0;   b = 8'd0;   cin = 1'b0;  #10;   // zero + zero, no carry
    a = 8'd0;   b = 8'd0;   cin = 1'b1;  #10;   // carry-in only
    a = 8'd255; b = 8'd0;   cin = 1'b0;  #10;   // max operand, sum = 255
    a = 8'd0;   b = 8'd255; cin = 1'b0;  #10;
    a = 8'd255; b = 8'd0;   cin = 1'b1;  #10;   // 255 + 1 -> overflow, sum = 0
    a = 8'd255; b = 8'd1;   cin = 1'b0;  #10;   // overflow, cout = 1
    a = 8'd128; b = 8'd128; cin = 1'b0;  #10;   // mid + mid -> overflow
    a = 8'd200; b = 8'd200; cin = 1'b1;  #10;   // high + high
    a = 8'd1;   b = 8'd1;   cin = 1'b0;  #10;   // low + low
    a = 8'd63;  b = 8'd64;  cin = 1'b0;  #10;   // low + mid, on the bin edge

    // a = 255 with b = 255 is deliberately NOT driven -- see the note above.

    $display("TB: finished");
    $finish;
  end

endmodule
