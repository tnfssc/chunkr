# OCR Server

OCR Server is a REST API server for OCR. It is built with Actix and Candle.

## Features

- [x] Health check
- [ ] OCR

## Build for CPU

```bash
cargo build
```

## Build for GPU

```bash
cargo build --features gpu
```

## Run

### For CPU

```bash
cargo run
```

### For GPU

```bash
cargo run --features gpu
```

