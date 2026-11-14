`timescale 1ns/1ps
module top_counter;

  counter_if intf();

  initial begin
    intf.clk = 1'b0;
    forever #5 intf.clk = ~intf.clk;
  end

  counter dut_inst (
    .clk (intf.clk), .rst_n (intf.rst_n), .en (intf.en), .count (intf.count));

  counter_coverage cov_inst (
    .clk (intf.clk), .rst_n (intf.rst_n), .en (intf.en), .count (intf.count));

  tb_counter tb_inst (
    .clk (intf.clk), .rst_n (intf.rst_n), .en (intf.en), .count (intf.count));

endmodule
