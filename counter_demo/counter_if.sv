`timescale 1ns/1ps
interface counter_if;
  logic       clk;
  logic       rst_n;
  logic       en;
  logic [3:0] count;
endinterface
