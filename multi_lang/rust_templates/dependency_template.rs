# Template: Cargo.toml manifest (raw). Placeholders substituted by RustDependencyGenerator.
[package]
name = "__MODULE_NAME__"
version = "0.1.0"
edition = "2021"

[dependencies]
actix-web = "4.4.1"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
diesel = { version = "2.1.0", features = ["postgres"] }

[dev-dependencies]
cargo-test = "0.1"