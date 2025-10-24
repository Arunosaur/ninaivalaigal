fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .file_descriptor_set_path("proto/graphops_descriptor.bin")
        .compile(
            &["../../shared/contracts/graphops/v1/graphops.proto"],
            &["../../shared/contracts/graphops/v1"],
        )?;

    Ok(())
}
