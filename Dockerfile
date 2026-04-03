# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy the Go source code
COPY matverse.kernel.go .

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o matverse.bin matverse.kernel.go

# Runtime stage
FROM alpine:latest

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/matverse.bin .

# Copy the web directory
COPY web/ ./web/

# Expose the port
EXPOSE 8765

# Run the application
CMD ["./matverse.bin"]
