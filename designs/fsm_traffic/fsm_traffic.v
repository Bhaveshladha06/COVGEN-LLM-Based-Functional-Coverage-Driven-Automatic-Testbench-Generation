// Traffic light FSM. Tests STATE and TRANSITION coverage -- the thing
// covergroups exist for, and which none of the designs tested so far exercise.
module fsm_traffic (clk, rst_n, sensor, red, yellow, green);
    input  clk, rst_n, sensor;
    output reg red, yellow, green;

    localparam S_RED = 2'd0, S_GREEN = 2'd1, S_YELLOW = 2'd2;

    reg [1:0] state;
    reg [3:0] timer;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_RED;
            timer <= 4'd0;
        end else begin
            case (state)
                S_RED: begin
                    if (timer >= 4'd5 && sensor) begin
                        state <= S_GREEN; timer <= 4'd0;
                    end else timer <= timer + 4'd1;
                end
                S_GREEN: begin
                    if (timer >= 4'd8) begin
                        state <= S_YELLOW; timer <= 4'd0;
                    end else timer <= timer + 4'd1;
                end
                S_YELLOW: begin
                    if (timer >= 4'd2) begin
                        state <= S_RED; timer <= 4'd0;
                    end else timer <= timer + 4'd1;
                end
                default: state <= S_RED;
            endcase
        end
    end

    always @(*) begin
        red    = (state == S_RED);
        yellow = (state == S_YELLOW);
        green  = (state == S_GREEN);
    end
endmodule
