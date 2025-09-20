class Ninaivalaigal < Formula
  desc "Exponential Memory (e^M) Agentic Execution Engine for Apple Container CLI"
  homepage "https://github.com/Arunosaur/ninaivalaigal"
  url "https://github.com/Arunosaur/ninaivalaigal/archive/refs/heads/main.tar.gz"
  version "1.0.0"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000" # Will be updated on release
  license "MIT"

  depends_on "container"
  depends_on "jq"
  depends_on "postgresql"
  depends_on "curl"
  depends_on "git"
  depends_on "make"

  # Only support Apple Silicon for optimal performance
  depends_on arch: :arm64

  def install
    # Install all files to libexec
    libexec.install Dir["*"]

    # Make scripts executable
    (libexec/"scripts").glob("*.sh").each { |script| script.chmod 0755 }

    # Create wrapper script
    (bin/"ninaivalaigal").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec make "$@"
    EOS

    # Create individual command shortcuts
    (bin/"nv-dev-up").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec make dev-up
    EOS

    (bin/"nv-dev-down").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec make dev-down
    EOS

    (bin/"nv-health").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec make health
    EOS

    (bin/"nv-status").write <<~EOS
      #!/bin/bash
      cd "#{libexec}" && exec make dev-status
    EOS
  end

  def post_install
    # Build required container images
    system "#{libexec}/scripts/build-images.sh" if File.exist?("#{libexec}/scripts/build-images.sh")
  end

  test do
    # Test that the main command works
    system bin/"ninaivalaigal", "--help"

    # Test that scripts are executable
    assert_predicate libexec/"scripts/nv-stack-start.sh", :executable?
    assert_predicate libexec/"scripts/nv-stack-stop.sh", :executable?

    # Test that Makefile exists
    assert_predicate libexec/"Makefile", :exist?
  end

  def caveats
    <<~EOS
      🚀 Ninaivalaigal has been installed!

      Quick Start:
        nv-dev-up      # Start development stack
        nv-health      # Check health status
        nv-status      # View detailed status
        nv-dev-down    # Stop stack

      Full Command Access:
        ninaivalaigal dev-up
        ninaivalaigal health
        ninaivalaigal tunnel-start REMOTE_HOST=server.com

      Documentation:
        #{libexec}/README.md
        #{libexec}/docs/APPLE_CONTAINER_CLI.md
        #{libexec}/docs/REMOTE_ACCESS_CLOUD.md

      Apple Container CLI Required:
        This formula requires Apple Container CLI for optimal ARM64 performance.
        If not installed: brew install container

      First Run:
        The first startup may take a few minutes to build container images.
        Subsequent runs will be much faster.
    EOS
  end
end
