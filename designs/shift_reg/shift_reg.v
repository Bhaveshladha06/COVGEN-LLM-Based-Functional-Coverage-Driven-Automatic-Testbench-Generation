// 8-bit shift register with parallel load. Tests sequential data movement and
// the interaction of two control signals that compete for the same register.
module shift_reg (clk, rst_n, load, shift_en, din, parallel_in, dout, serial_out);
    input        clk, rst_n, load, shift_en, din;
    input  [7:0] parallel_in;
    output [7:0] dout;
    output       serial_out;

    reg [7:0] shift_data;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)          shift_data <= 8'd0;
        else if (load)       shift_data <= parallel_in;
        else if (shift_en)   shift_data <= {shift_data[6:0], din};
    end

    assign dout       = shift_data;
    assign serial_out = shift_data[7];
endmodule
