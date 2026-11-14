// 8-bit adder with carry in and carry out. Combinational: no clock, no reset.
module adder8 (a, b, cin, sum, cout);
    input  [7:0] a;
    input  [7:0] b;
    input        cin;
    output [7:0] sum;
    output       cout;

    assign {cout, sum} = a + b + cin;
endmodule
