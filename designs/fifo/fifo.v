module fifo (clk, rst_n, wr_en, rd_en, din, dout, full, empty, count);
    input             clk;
    input             rst_n;
    input             wr_en;
    input             rd_en;
    input      [7:0]  din;
    output reg [7:0]  dout;
    output            full;
    output            empty;
    output reg [3:0]  count;

    reg [7:0] mem [0:7];
    reg [2:0] wptr, rptr;

    assign full  = (count == 4'd8);
    assign empty = (count == 4'd0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wptr  <= 3'd0;
            rptr  <= 3'd0;
            count <= 4'd0;
            dout  <= 8'd0;
        end else begin
            if (wr_en && !full) begin
                mem[wptr] <= din;
                wptr      <= wptr + 3'd1;
            end
            if (rd_en && !empty) begin
                dout <= mem[rptr];
                rptr <= rptr + 3'd1;
            end
            case ({wr_en && !full, rd_en && !empty})
                2'b10:   count <= count + 4'd1;
                2'b01:   count <= count - 4'd1;
                default: count <= count;
            endcase
        end
    end
endmodule
