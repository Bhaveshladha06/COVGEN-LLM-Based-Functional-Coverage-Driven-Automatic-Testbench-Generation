// Valid/ready handshake buffer. Tests protocol coverage: the interesting cases
// are the stalls, not the transfers.
module handshake (clk, rst_n, in_valid, in_data, in_ready,
                  out_valid, out_data, out_ready);
    input        clk, rst_n;
    input        in_valid;
    input  [7:0] in_data;
    output       in_ready;
    output reg   out_valid;
    output reg [7:0] out_data;
    input        out_ready;

    assign in_ready = !out_valid || out_ready;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_valid <= 1'b0;
            out_data  <= 8'd0;
        end else begin
            if (in_valid && in_ready) begin
                out_valid <= 1'b1;
                out_data  <= in_data;
            end else if (out_ready) begin
                out_valid <= 1'b0;
            end
        end
    end
endmodule
