# Changelog

All notable changes to the ninaivalaigal project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## <small>1.4.6 (2025-09-20)</small>

* fix: add longer wait for database readiness before PgBouncer health check ([45773a3cbd38901ad26a18d03f4055751f660ccc](https://github.com/Arunosaur/ninaivalaigal/commit/45773a3cbd38901ad26a18d03f4055751f660ccc))

## <small>1.4.5 (2025-09-20)</small>

* fix: use direct IP 127.0.0.1 instead of host aliases for Apple Container CLI ([b8a150cf8c5cd26a5da37e4c300daf00034cfa45](https://github.com/Arunosaur/ninaivalaigal/commit/b8a150cf8c5cd26a5da37e4c300daf00034cfa45))

## <small>1.4.4 (2025-09-20)</small>

* fix: use host.lima.internal for Apple Container CLI networking ([f9e47ab6078d269dc35ed5c6b03ba9e61952917c](https://github.com/Arunosaur/ninaivalaigal/commit/f9e47ab6078d269dc35ed5c6b03ba9e61952917c))

## <small>1.4.3 (2025-09-20)</small>

* fix: align database credentials across all components ([d60af6f7821fc0bf79f2719479906ddc0075775a](https://github.com/Arunosaur/ninaivalaigal/commit/d60af6f7821fc0bf79f2719479906ddc0075775a))

## <small>1.4.2 (2025-09-20)</small>

* fix: replace container ps with container logs for Apple Container CLI compatibility ([2126ee6c52c2dadd5576816eec581d307dc7fa76](https://github.com/Arunosaur/ninaivalaigal/commit/2126ee6c52c2dadd5576816eec581d307dc7fa76))
* debug: add container detection debugging to identify Apple Container CLI format ([98879b17dcbd1879aff146bd89d7455a04ed8d9d](https://github.com/Arunosaur/ninaivalaigal/commit/98879b17dcbd1879aff146bd89d7455a04ed8d9d))

## <small>1.4.1 (2025-09-20)</small>

* fix: simplify container detection for Apple Container CLI compatibility ([485d05e0cba9b036e98801936e50a607bc08b8b3](https://github.com/Arunosaur/ninaivalaigal/commit/485d05e0cba9b036e98801936e50a607bc08b8b3))

## 1.4.0 (2025-09-19)

* feat: implement comprehensive defensive scripts for robust stack startup ([316dafb3994f63064a0eacad1e803b3a81333e50](https://github.com/Arunosaur/ninaivalaigal/commit/316dafb3994f63064a0eacad1e803b3a81333e50))

## <small>1.3.22 (2025-09-19)</small>

* fix: add timeouts and debugging to prevent hanging workflows ([708b115df9e4007787b753136c513a1e611fec87](https://github.com/Arunosaur/ninaivalaigal/commit/708b115df9e4007787b753136c513a1e611fec87))

## <small>1.3.21 (2025-09-19)</small>

* fix: add non-root user to PgBouncer for security compliance ([f9726080c613b03dc0bdf16de2460bbc87930e63](https://github.com/Arunosaur/ninaivalaigal/commit/f9726080c613b03dc0bdf16de2460bbc87930e63))

## <small>1.3.20 (2025-09-19)</small>

* fix: use repo root as build context for API image ([526441efaa03f1e18f7a9e2a5c2520985a7c7aaf](https://github.com/Arunosaur/ninaivalaigal/commit/526441efaa03f1e18f7a9e2a5c2520985a7c7aaf))

## <small>1.3.19 (2025-09-19)</small>

* fix: correct Docker build context for container images ([e6db01f598f56bad81be6aed29c90db4ea042a16](https://github.com/Arunosaur/ninaivalaigal/commit/e6db01f598f56bad81be6aed29c90db4ea042a16))

## <small>1.3.18 (2025-09-19)</small>

* fix: add missing userlist.txt for PgBouncer Docker build ([f7428d9982ff813c23f6ab7fb1846a5bdd26be00](https://github.com/Arunosaur/ninaivalaigal/commit/f7428d9982ff813c23f6ab7fb1846a5bdd26be00))

## <small>1.3.17 (2025-09-19)</small>

* fix: comprehensive rock-solid Apple Container CLI solution ([b0a4277c580615a09819472b377d059fd9d5d5c0](https://github.com/Arunosaur/ninaivalaigal/commit/b0a4277c580615a09819472b377d059fd9d5d5c0))

## <small>1.3.16 (2025-09-19)</small>

* fix: add forced user for auth_type=any in PgBouncer config ([be87b32d5692a64825b352cad423c7229d1f06ee](https://github.com/Arunosaur/ninaivalaigal/commit/be87b32d5692a64825b352cad423c7229d1f06ee))

## <small>1.3.15 (2025-09-19)</small>

* fix: use auth_type=any for PgBouncer to bypass authentication issues ([004fe3c1d445ba1d458734a0d82b9376d5c16433](https://github.com/Arunosaur/ninaivalaigal/commit/004fe3c1d445ba1d458734a0d82b9376d5c16433))

## <small>1.3.14 (2025-09-19)</small>

* fix: improve PgBouncer script with better debugging and image building ([b9a01b50596d68ac14470a504a95c9fc3ccc8e35](https://github.com/Arunosaur/ninaivalaigal/commit/b9a01b50596d68ac14470a504a95c9fc3ccc8e35))

## <small>1.3.13 (2025-09-19)</small>

* fix: use proven production scripts instead of reinventing ([99d2847ff53e09d405753b702f0362cc64aac6f7](https://github.com/Arunosaur/ninaivalaigal/commit/99d2847ff53e09d405753b702f0362cc64aac6f7))

## <small>1.3.12 (2025-09-19)</small>

* fix: resolve API JWT_SECRET and PgBouncer pidfile issues ([90e3c125b8101074a86d1ee50b3339dbd1dd0f7f](https://github.com/Arunosaur/ninaivalaigal/commit/90e3c125b8101074a86d1ee50b3339dbd1dd0f7f))

## <small>1.3.11 (2025-09-19)</small>

* fix: API container networking for Lima environment ([7ca660d420d31fac55235becf5af508de8264b77](https://github.com/Arunosaur/ninaivalaigal/commit/7ca660d420d31fac55235becf5af508de8264b77))

## <small>1.3.10 (2025-09-19)</small>

* fix: critical fixes for PgBouncer host and image building ([49dd78a2654b63133d4d324fbfa0882287e78e6a](https://github.com/Arunosaur/ninaivalaigal/commit/49dd78a2654b63133d4d324fbfa0882287e78e6a))

## <small>1.3.9 (2025-09-19)</small>

* fix: comprehensive drop-in solution for Mac Studio green CI ([eb5f9a043054b0d77622bbe4a6c503b399ff4e62](https://github.com/Arunosaur/ninaivalaigal/commit/eb5f9a043054b0d77622bbe4a6c503b399ff4e62))

## <small>1.3.8 (2025-09-19)</small>

* fix: comprehensive solution for all CI failures ([ce2f54b0008f0a9efd0da0d60e270ce673cb4dc7](https://github.com/Arunosaur/ninaivalaigal/commit/ce2f54b0008f0a9efd0da0d60e270ce673cb4dc7))

## <small>1.3.7 (2025-09-19)</small>

* fix: resolve PgBouncer auth mismatch with robust testing ([45502e473c5597a2ee30d1529a9e13707020943e](https://github.com/Arunosaur/ninaivalaigal/commit/45502e473c5597a2ee30d1529a9e13707020943e))

## <small>1.3.6 (2025-09-19)</small>

* fix: use proven nina-pgbouncer:arm64 image without defensive checks ([3a68ef4036e414f510c0a62075ece50e00e2af1a](https://github.com/Arunosaur/ninaivalaigal/commit/3a68ef4036e414f510c0a62075ece50e00e2af1a))

## <small>1.3.5 (2025-09-19)</small>

* fix: comprehensive workflow and PgBouncer auth fixes ([8ab610a0c993bca41100570f003375b90181848e](https://github.com/Arunosaur/ninaivalaigal/commit/8ab610a0c993bca41100570f003375b90181848e))

## <small>1.3.4 (2025-09-19)</small>

* fix: use existing custom nina-pgbouncer:arm64 image ([fe229e1c40d89f44955c1b1885fe0b61daf0d860](https://github.com/Arunosaur/ninaivalaigal/commit/fe229e1c40d89f44955c1b1885fe0b61daf0d860))

## <small>1.3.3 (2025-09-19)</small>

* fix: use safe user-space container CLI setup (no sudo) ([8bfc2ce17076119755b508cf652ca754409342e7](https://github.com/Arunosaur/ninaivalaigal/commit/8bfc2ce17076119755b508cf652ca754409342e7))

## <small>1.3.2 (2025-09-19)</small>

* fix: implement robust container CLI and pre-commit fixes ([d11b53cbd580b1f5cb17cf268be6c07b53de9f92](https://github.com/Arunosaur/ninaivalaigal/commit/d11b53cbd580b1f5cb17cf268be6c07b53de9f92))
* fix: robust fallbacks for container pull and Python dependency issues ([2621f775290907fed75c9c9bc847895c9c898392](https://github.com/Arunosaur/ninaivalaigal/commit/2621f775290907fed75c9c9bc847895c9c898392))

## <small>1.3.1 (2025-09-19)</small>

* fix: resolve Python dependencies and container CLI issues ([b0a19c078c50d0e0a610e903028e3e96a3f86a17](https://github.com/Arunosaur/ninaivalaigal/commit/b0a19c078c50d0e0a610e903028e3e96a3f86a17))

## 1.3.0 (2025-09-19)

* feat: add runner smoke test for hybrid architecture ([9d09c911fc0e0e87006e25aa2cde5af5a349b611](https://github.com/Arunosaur/ninaivalaigal/commit/9d09c911fc0e0e87006e25aa2cde5af5a349b611))
* test: trigger Mac Studio runner after restart ([c62f688aa49eb4d4b122eee9492aad8485d40a49](https://github.com/Arunosaur/ninaivalaigal/commit/c62f688aa49eb4d4b122eee9492aad8485d40a49))

## <small>1.2.1 (2025-09-19)</small>

* fix: use targeted release assets instead of wildcard docs ([fd65da6cad83f2a4b0b4756758ea02ce121c3ff5](https://github.com/Arunosaur/ninaivalaigal/commit/fd65da6cad83f2a4b0b4756758ea02ce121c3ff5))

## 1.2.0 (2025-09-19)

* fix: Add clean YAML workflow to resolve CI failures ([512d48cb9b82bd77219f06d88c3a19f4bb2eaa74](https://github.com/Arunosaur/ninaivalaigal/commit/512d48cb9b82bd77219f06d88c3a19f4bb2eaa74))
* fix: Add GitHub PAT support for semantic-release workflow ([fe3bbec1d601bd527fe53ae739102b8c0d31f51f](https://github.com/Arunosaur/ninaivalaigal/commit/fe3bbec1d601bd527fe53ae739102b8c0d31f51f))
* fix: add missing conventional-changelog-conventionalcommits dependency ([8b7ca724f6aae817d25275e10f9320dd14ab0557](https://github.com/Arunosaur/ninaivalaigal/commit/8b7ca724f6aae817d25275e10f9320dd14ab0557))
* fix: bulletproof semantic-release with proper token wiring ([82dd43f4c61b840f3c59e2d328f1e13cb5f1ca1d](https://github.com/Arunosaur/ninaivalaigal/commit/82dd43f4c61b840f3c59e2d328f1e13cb5f1ca1d))
* fix: Clean semantic-release workflow with local dependencies ([6ff6f5b6fa52afaaf1deca083ad0df465d4261e4](https://github.com/Arunosaur/ninaivalaigal/commit/6ff6f5b6fa52afaaf1deca083ad0df465d4261e4))
* fix: Convert .releaserc.json to YAML format to resolve JSON parsing errors ([0481d9db075c994d24e00d06e792751e9cd5b057](https://github.com/Arunosaur/ninaivalaigal/commit/0481d9db075c994d24e00d06e792751e9cd5b057))
* fix: Disable conflicting workflows causing CI failures ([5aa1f95a2280a8096fa162a5e79808d0ba800280](https://github.com/Arunosaur/ninaivalaigal/commit/5aa1f95a2280a8096fa162a5e79808d0ba800280))
* fix: handle malformed commit dates in release notes generation ([81e7c0b36541bc4ea44aa6724e860248792ce276](https://github.com/Arunosaur/ninaivalaigal/commit/81e7c0b36541bc4ea44aa6724e860248792ce276))
* fix: Remove package.json reference to old .releaserc.json ([4f6d4401ef68122bbfc2833759c3f9d29d783fb8](https://github.com/Arunosaur/ninaivalaigal/commit/4f6d4401ef68122bbfc2833759c3f9d29d783fb8))
* fix: resolve Apple Container CLI script issues ([c1a9618520d7c3b2981fe756c2cc6b94c8c933d4](https://github.com/Arunosaur/ninaivalaigal/commit/c1a9618520d7c3b2981fe756c2cc6b94c8c933d4))
* fix: update GH_TOKEN with working classic token ([e391c3af9671400674f9f8777eaae77a1bbc04bd](https://github.com/Arunosaur/ninaivalaigal/commit/e391c3af9671400674f9f8777eaae77a1bbc04bd))
* fix: Use nina conda env + Python version agnostic pre-commit ([849de418a2666c269cf0cd7ba53e5bd954ed3461](https://github.com/Arunosaur/ninaivalaigal/commit/849de418a2666c269cf0cd7ba53e5bd954ed3461))
* feat: Add Apple Container CLI scripts for Mac Studio ([621d43ae8eaeae5b121d34041d4d50e81cfce0db](https://github.com/Arunosaur/ninaivalaigal/commit/621d43ae8eaeae5b121d34041d4d50e81cfce0db))
* feat: Add complete Mac Studio CI/CD workflows and mem0 sidecar ([4f20c6e23abb89ad9bb5510fda0a5194abafe7a5](https://github.com/Arunosaur/ninaivalaigal/commit/4f20c6e23abb89ad9bb5510fda0a5194abafe7a5))
* feat: Add hardened validation and production fixes ([2bcb74767680856f1ae0cf1c58c19775733deb30](https://github.com/Arunosaur/ninaivalaigal/commit/2bcb74767680856f1ae0cf1c58c19775733deb30))
* feat: Add incremental deployment scripts for Mac Studio ([342e72c36a07a903dd4b2e926783032680fd662f](https://github.com/Arunosaur/ninaivalaigal/commit/342e72c36a07a903dd4b2e926783032680fd662f))
* feat: Add Mac Studio Apple Container CLI validation workflow ([13d0b321aef2eeed6a8ae52d3fa09615cef7495c](https://github.com/Arunosaur/ninaivalaigal/commit/13d0b321aef2eeed6a8ae52d3fa09615cef7495c))
* feat: Add Mac Studio CI/CD workflow and runner setup guide ([a9d5c8f23f6b439849e3afc1673e671801995b33](https://github.com/Arunosaur/ninaivalaigal/commit/a9d5c8f23f6b439849e3afc1673e671801995b33))
* feat: Add minimal Mac Studio test workflow ([cc068f907ca7dd5608e2cbafdd8f90d1fa921365](https://github.com/Arunosaur/ninaivalaigal/commit/cc068f907ca7dd5608e2cbafdd8f90d1fa921365))
* feat: Add pre-merge validation and archive safety guards ([9e26daa897340c1b7c7963956ffa5d8497cdca41](https://github.com/Arunosaur/ninaivalaigal/commit/9e26daa897340c1b7c7963956ffa5d8497cdca41))
* feat: Add production readiness suite - backups, monitoring, security, and cutover procedures ([6d1cc42169c7117f8dff5363d5b98ed71ee44b8f](https://github.com/Arunosaur/ninaivalaigal/commit/6d1cc42169c7117f8dff5363d5b98ed71ee44b8f))
* feat: add production validation and next steps documentation ([6103c7a7616a778fc4791539eb650531b2ebc102](https://github.com/Arunosaur/ninaivalaigal/commit/6103c7a7616a778fc4791539eb650531b2ebc102))
* feat: Apple Container CLI breakthrough - production validated ([47334bf7fe1e963cffbc94b543506548530ca04c](https://github.com/Arunosaur/ninaivalaigal/commit/47334bf7fe1e963cffbc94b543506548530ca04c))
* feat: CI fixes + SPEC-010 observability implementation ([9a5b241b1b623fbc1dbc41fd7c2efd7860691f10](https://github.com/Arunosaur/ninaivalaigal/commit/9a5b241b1b623fbc1dbc41fd7c2efd7860691f10))
* feat: COMPLETE Apple Container CLI stack - MISSION ACCOMPLISHED! 🎉 ([a5e3e40dde395d2b1dcd5c3b646ce6b05df34442](https://github.com/Arunosaur/ninaivalaigal/commit/a5e3e40dde395d2b1dcd5c3b646ce6b05df34442))
* feat: Complete enterprise stack - SPEC automation + 5-service UI containerization ([7c970de8edb13fc1b463108d94e06889150f29d6](https://github.com/Arunosaur/ninaivalaigal/commit/7c970de8edb13fc1b463108d94e06889150f29d6))
* feat: complete PR 6 - governance & releases with Mac Studio production setup ([c6169db1856f3adf27c4bc9a64bfd6243bb49ebc](https://github.com/Arunosaur/ninaivalaigal/commit/c6169db1856f3adf27c4bc9a64bfd6243bb49ebc))
* feat: custom ARM64 API image and comprehensive documentation ([481ba6e5696fd4a9fee298deac623f27bd16d92a](https://github.com/Arunosaur/ninaivalaigal/commit/481ba6e5696fd4a9fee298deac623f27bd16d92a))
* feat: custom ARM64 PgBouncer for Apple Container CLI ([d83a65a47bcddb01976e4ad58e188ec724d11085](https://github.com/Arunosaur/ninaivalaigal/commit/d83a65a47bcddb01976e4ad58e188ec724d11085))
* feat: Deployment-aware system detection for VM/cloud/container compatibility ([5b7fcdfcaec18a9bc49e5dad32a82fb1f6115549](https://github.com/Arunosaur/ninaivalaigal/commit/5b7fcdfcaec18a9bc49e5dad32a82fb1f6115549))
* feat: Enhanced SPEC workflow with intelligent system detection and recommendations ([e2fbdc1dbffba8c4312e5cf8a0a523ff71ea9e20](https://github.com/Arunosaur/ninaivalaigal/commit/e2fbdc1dbffba8c4312e5cf8a0a523ff71ea9e20))
* feat: Finalize production-ready Apple Container CLI stack ([b291ddae084bdb439dd987e2c27d082073a9d056](https://github.com/Arunosaur/ninaivalaigal/commit/b291ddae084bdb439dd987e2c27d082073a9d056))
* feat: Harden mem0 integration with production patterns and comprehensive error handling ([fc0de6b96ae0e5bd4620824ba1d4feaf91ffff1f](https://github.com/Arunosaur/ninaivalaigal/commit/fc0de6b96ae0e5bd4620824ba1d4feaf91ffff1f))
* feat: PR 1 - Supply chain hardening with pinned images, SBOM, and vulnerability scanning ([9747208bf1506f2b6aa71be21862e3fbd8d940c4](https://github.com/Arunosaur/ninaivalaigal/commit/9747208bf1506f2b6aa71be21862e3fbd8d940c4))
* feat: PR 2 - Pre-commit hooks with secrets scanning and comprehensive code quality ([e946a71f503abca690922f8181d0f7f57536af73](https://github.com/Arunosaur/ninaivalaigal/commit/e946a71f503abca690922f8181d0f7f57536af73))
* feat: PR 3 - Backup verification with restore rehearsal and automated CI monitoring ([0d0577953299a27630d26aef0f0405c3d01ccb9d](https://github.com/Arunosaur/ninaivalaigal/commit/0d0577953299a27630d26aef0f0405c3d01ccb9d))
* feat: PR 4 - Observability and SLO monitoring with Prometheus metrics and health checks ([b79989585a75338e90bd487fbeaa01602ba48efb](https://github.com/Arunosaur/ninaivalaigal/commit/b79989585a75338e90bd487fbeaa01602ba48efb))
* feat: PR 5 - mem0 sidecar authentication with shared secret and HMAC support ([378cbd27f31c3897490306c98574594225e3f163](https://github.com/Arunosaur/ninaivalaigal/commit/378cbd27f31c3897490306c98574594225e3f163))
* feat: PR 6 - Governance and automated releases with semantic-release ([1b9c251b13902ac9f9be9d9af9221caf0f4bac31](https://github.com/Arunosaur/ninaivalaigal/commit/1b9c251b13902ac9f9be9d9af9221caf0f4bac31))
* feat: Reusable conda nina action for consistent environment ([4aff05a71d3aa895c8f987ef1390ab676680805e](https://github.com/Arunosaur/ninaivalaigal/commit/4aff05a71d3aa895c8f987ef1390ab676680805e))
* feat: simplified release workflow using GitHub CLI ([e48ee75cd3aa1b9438d0c62044d2b39dff6fcdbd](https://github.com/Arunosaur/ninaivalaigal/commit/e48ee75cd3aa1b9438d0c62044d2b39dff6fcdbd))
* feat: SPEC-012 Memory Substrate implementation ([1c0c023f8f86dd223ae2c99b2331c5792410d11a](https://github.com/Arunosaur/ninaivalaigal/commit/1c0c023f8f86dd223ae2c99b2331c5792410d11a))
* feat: test semantic-release with GH_TOKEN ([a1e8019ee272f8e22cf852a118bcbce1e82cddbf](https://github.com/Arunosaur/ninaivalaigal/commit/a1e8019ee272f8e22cf852a118bcbce1e82cddbf))
* feat: Wire mem0 into stack orchestration as first-class service ([0b09fa66bbb80b0372faeabeaa9fce6afe36baa7](https://github.com/Arunosaur/ninaivalaigal/commit/0b09fa66bbb80b0372faeabeaa9fce6afe36baa7))
* chore: Add .env to .gitignore to prevent password leaks ([bbe21842194df970d0901b62bcfbe69c4870c96f](https://github.com/Arunosaur/ninaivalaigal/commit/bbe21842194df970d0901b62bcfbe69c4870c96f))
* chore: add SPEC-013 as external submodule ([615db8fd64e11b490b785f37aadf104712fbc4d6](https://github.com/Arunosaur/ninaivalaigal/commit/615db8fd64e11b490b785f37aadf104712fbc4d6))
* chore: add weekly dependency updates and enhanced PR template ([421bb03eec59ed7a68c64d9773a81334b8d94403](https://github.com/Arunosaur/ninaivalaigal/commit/421bb03eec59ed7a68c64d9773a81334b8d94403))
* chore: cleanup test file ([79308f4b9526d269bb38a79e145e94cd3d3283cf](https://github.com/Arunosaur/ninaivalaigal/commit/79308f4b9526d269bb38a79e145e94cd3d3283cf))
* chore: Move SPEC-013 to external submodule (Option C) ([901bdc1164af6f010188282742549064275705ec](https://github.com/Arunosaur/ninaivalaigal/commit/901bdc1164af6f010188282742549064275705ec))
* trigger: Test clean Mac Studio workflow ([cf29668b1266d29ed533d74ecc09266833b536cb](https://github.com/Arunosaur/ninaivalaigal/commit/cf29668b1266d29ed533d74ecc09266833b536cb))
* trigger: Test nina conda environment integration ([45342faa3b5e7461b921e0a3c5db71379fb8fb4e](https://github.com/Arunosaur/ninaivalaigal/commit/45342faa3b5e7461b921e0a3c5db71379fb8fb4e))
* trigger: Test reusable conda nina action ([22603848482538abd4b45ec13f804477bb65a0f1](https://github.com/Arunosaur/ninaivalaigal/commit/22603848482538abd4b45ec13f804477bb65a0f1))
* docs: Add Apple Container CLI Quickstart to README ([8722ced434b72a8de3d4d6fb9a44d2d24ac329fb](https://github.com/Arunosaur/ninaivalaigal/commit/8722ced434b72a8de3d4d6fb9a44d2d24ac329fb))
* docs: Add comprehensive Apple Container CLI documentation ([3ff888537068b98b872040046d0fe6d041274bca](https://github.com/Arunosaur/ninaivalaigal/commit/3ff888537068b98b872040046d0fe6d041274bca))
* docs: Add Mac Studio production deployment guide ([1142bafd405ba6d1d1b470e351405b4b5a3c642a](https://github.com/Arunosaur/ninaivalaigal/commit/1142bafd405ba6d1d1b470e351405b4b5a3c642a))
* docs: Add v1.1.0 changelog for multipart security hardening release ([f47b3512e2704eb6e7b8ce95ca8bde6342a771ce](https://github.com/Arunosaur/ninaivalaigal/commit/f47b3512e2704eb6e7b8ce95ca8bde6342a771ce))
* docs: Production Ready Summary - Complete Success Report ([258dc6a3a23889371176365b2241cf9e69faaf1a](https://github.com/Arunosaur/ninaivalaigal/commit/258dc6a3a23889371176365b2241cf9e69faaf1a))
* Add comprehensive validation scripts for Mac Studio deployment ([038c90eb0ba5e72b308b6b414650545b2d0e0aff](https://github.com/Arunosaur/ninaivalaigal/commit/038c90eb0ba5e72b308b6b414650545b2d0e0aff))
* Add Mac Studio setup guide ([5fcc09f57975d5b931e5b77c7b6e556552c9120c](https://github.com/Arunosaur/ninaivalaigal/commit/5fcc09f57975d5b931e5b77c7b6e556552c9120c))
* Add Windsurf context sync for Mac Studio setup ([8e01b769e0baaaa5e5df3d38f48f8be86b047f6a](https://github.com/Arunosaur/ninaivalaigal/commit/8e01b769e0baaaa5e5df3d38f48f8be86b047f6a))
* Apply production-grade observability fixes and operational improvements ([8224d3333378b8ca9bb45d65748e3bf715a2cbcc](https://github.com/Arunosaur/ninaivalaigal/commit/8224d3333378b8ca9bb45d65748e3bf715a2cbcc))
* Apply security ops polish: config hash + traceparent + JWT replay + CI gates ([ae7fb07f8cd349f59b843c877341d43778252667](https://github.com/Arunosaur/ninaivalaigal/commit/ae7fb07f8cd349f59b843c877341d43778252667))
* Apply Spec 009 hardening patch: RBAC metrics + JWKS resilience + 401/403 semantics ([35a4f378a9131e3b4afe32fd31b4d9f52b01166b](https://github.com/Arunosaur/ninaivalaigal/commit/35a4f378a9131e3b4afe32fd31b4d9f52b01166b))
* Complete file organization + Spec 011.1 memory substrate integration ([415f56fb5e7a052ace919a31a425117eb2bcb3d5](https://github.com/Arunosaur/ninaivalaigal/commit/415f56fb5e7a052ace919a31a425117eb2bcb3d5))
* Complete observability package integration with SLO monitoring ([8a02b70f2c545fabe2183e7d0257423986efda50](https://github.com/Arunosaur/ninaivalaigal/commit/8a02b70f2c545fabe2183e7d0257423986efda50))
* Complete RBAC integration with CI/CD improvements and production readiness ([d18d00e3468a54cddc8d0897742dc2c032c5859b](https://github.com/Arunosaur/ninaivalaigal/commit/d18d00e3468a54cddc8d0897742dc2c032c5859b))
* Complete Spec 009: JWT/RBAC integration with real claims resolver ([4b845659d8c9352861582236d29434f3ec7c1c8f](https://github.com/Arunosaur/ninaivalaigal/commit/4b845659d8c9352861582236d29434f3ec7c1c8f))
* Deploy Spec 010 kickoff scaffolding: tracing + RED metrics + dashboards + alerts ([7f53529c25348f1a14c98b7af88071cd21b5cf63](https://github.com/Arunosaur/ninaivalaigal/commit/7f53529c25348f1a14c98b7af88071cd21b5cf63))
* Deploy Spec 011.1 Factory: Auto-select Postgres/InMemory + FastAPI wiring ([ca51d22262f80a16d46dbea178fb1afa00756597](https://github.com/Arunosaur/ninaivalaigal/commit/ca51d22262f80a16d46dbea178fb1afa00756597))
* Deploy Spec 011.1: Production Postgres + pgvector semantic search ([09d7abeec557759ac181b472f3fc8537df3ad543](https://github.com/Arunosaur/ninaivalaigal/commit/09d7abeec557759ac181b472f3fc8537df3ad543))
* Implement advanced security middleware enhancements based on external code review ([a07247094539b7be157c462d5b15948a3e56ccce](https://github.com/Arunosaur/ninaivalaigal/commit/a07247094539b7be157c462d5b15948a3e56ccce))
* Implement centralized security middleware with intelligent redaction ([5df8bc3ec2879bf6a37d1acb6426b7ccecd0890e](https://github.com/Arunosaur/ninaivalaigal/commit/5df8bc3ec2879bf6a37d1acb6426b7ccecd0890e))
* Implement comprehensive multipart security monitoring system ([6039b81da00f95e8204571507b3069d35d8a5f34](https://github.com/Arunosaur/ninaivalaigal/commit/6039b81da00f95e8204571507b3069d35d8a5f34))
* Implement enhanced security middleware with streaming redaction and comprehensive testing ([3be9cb2e71d43f223b04c95ef536df1587b5ad76](https://github.com/Arunosaur/ninaivalaigal/commit/3be9cb2e71d43f223b04c95ef536df1587b5ad76))
* Implement production-grade monitoring improvements and CI validation ([4ecfcf458100e6f8775fad0777491095bf928aa4](https://github.com/Arunosaur/ninaivalaigal/commit/4ecfcf458100e6f8775fad0777491095bf928aa4))
* Launch Spec 011: Memory substrate with FastAPI + MCP dual architecture ([60d381a03b2ec33f56c66ce5fd4a8103bc784c51](https://github.com/Arunosaur/ninaivalaigal/commit/60d381a03b2ec33f56c66ce5fd4a8103bc784c51))
* Merge branch 'security-middleware-implementation' ([65b4311b4fc58300af11c11260171b4c6d1b1ca1](https://github.com/Arunosaur/ninaivalaigal/commit/65b4311b4fc58300af11c11260171b4c6d1b1ca1))
* Update STATE.md with enterprise security architecture planning and ecosystem vision analysis ([804c0e0b36f624f017530b5bef30a631ea4d289f](https://github.com/Arunosaur/ninaivalaigal/commit/804c0e0b36f624f017530b5bef30a631ea4d289f))

# Changelog

## [1.1.0] - 2025-09-16

### 🔒 Major Security Release: Multipart Upload Hardening

#### Multipart Security Framework
- **Hardened Starlette Adapter**: Stream-time per-part size enforcement with early abort
- **Part Count DoS Prevention**: Configurable limits (default: 256 parts) with HTTP 413 responses
- **Binary Masquerade Detection**: Enhanced magic byte detection (PE, ELF, Mach-O, Java, MP4 offset-aware)
- **Archive Blocking**: ZIP/RAR/7Z prevention on text-only endpoints with HTTP 415 responses
- **UTF-8 Validation**: Strict text encoding with UTF-16 detection and rejection
- **Content-Transfer-Encoding Guards**: Base64/quoted-printable blocking to prevent encoding bypasses

#### Security Controls Matrix
- **DoS Prevention**: Part count and size limits prevent resource exhaustion
- **Code Injection**: Magic byte detection blocks executable uploads  
- **Data Exfiltration**: Archive blocking prevents nested payload smuggling
- **Encoding Attacks**: CTE guards prevent base64/quoted-printable bypasses
- **Unicode Exploits**: Strict UTF-8 validation prevents encoding confusion

#### Filename Security
- **Unicode Normalization**: NFC normalization with path traversal prevention
- **Reserved Name Handling**: Windows reserved name protection (CON, PRN, AUX, etc.)
- **Content-Disposition Parsing**: RFC 5987 encoded filename support
- **Archive Detection**: Comprehensive extension validation with safety checks

#### Testing & Validation
- **Focused Testing Framework**: 6 hardening tests with MultiPartParser mocking
- **27/27 Tests Passing**: Complete security control validation
- **Isolated Unit Tests**: No external dependencies with fast execution
- **CI/CD Integration**: Ready for automated security validation

#### Monitoring & Health
- **Metrics Integration**: Bounded cardinality rejection reasons
- **Health Monitoring**: `/healthz/config` multipart validation
- **Boot Validation**: Production failure detection with actionable messages
- **Debug Support**: Comprehensive logging and troubleshooting guides

#### RBAC Policy Protection
- **Pre-commit Gate**: Prevents unnoticed RBAC matrix changes
- **Baseline Snapshots**: Automated policy drift detection
- **Privilege Escalation Detection**: Security-critical change validation
- **Manual Approval Workflow**: Configurable thresholds with bypass protection

#### Performance Characteristics
- **Stream Processing**: O(1) memory usage regardless of upload size
- **Early Abort**: Violations detected within first few KB
- **Minimal Overhead**: ~1-2ms per part for security validation
- **Bounded Cardinality**: Metrics labels limited to prevent explosion

### Added
- `server/security/multipart/starlette_adapter.py` - Hardened multipart adapter
- `server/utils/filename_sanitizer.py` - Filename security utilities
- `server/health/multipart_config.py` - Health monitoring integration
- `docs/security/MULTIPART_SECURITY_CONSOLIDATED.md` - Complete security guide
- `tests/test_starlette_adapter_hardening.py` - Focused security tests
- `tests/test_filename_sanitizer.py` - Filename safety validation

### Security Improvements
- Stream-time enforcement prevents memory exhaustion attacks
- Part count limiting blocks multipart DoS vectors
- Binary masquerade detection prevents executable smuggling
- Archive blocking on text endpoints prevents payload nesting
- UTF-8 validation with CTE guards prevents encoding bypasses
- RBAC policy snapshot gate prevents privilege drift

### Breaking Changes
- Multipart adapter surface changes require integration updates
- New HTTPException status codes (413, 415) for security violations
- Stricter validation may reject previously accepted uploads

### Migration Guide
- Update multipart handlers to use new `scan_with_starlette` function
- Add health check integration for production monitoring
- Review and adjust size/count limits for your use case
- Test existing uploads against new security controls

---

## [1.0.0-ninaivalaigal] - 2025-09-13

### 🎉 Major Release: Complete Rebranding to Ninaivalaigal

#### Brand Identity
- **Product Name**: mem0 → Ninaivalaigal (Tamil: memories/recollections)
- **Command Agent**: @mem0 → @e^M (exponential Memory)
- **Company**: Medhays (www.medhasys.com)
- **Vision**: Foundation for broader AI ecosystem (SmritiOS, TarangAI, Pragna, FluxMind)

#### Frontend UI
- Updated all HTML pages (signup.html, login.html, dashboard.html)
- Changed titles from "mem0" to "Ninaivalaigal"
- Updated descriptions from "AI Memory" to "e^M Memory"
- Rebranded welcome messages and navigation

#### CLI & Commands
- Created new CLI clients: `eM.py` and `client/eM`
- Command invocation: `mem0` → `eM`
- Updated all error messages and help text
- Preserved all existing functionality

#### Configuration & Environment
- New config file: `ninaivalaigal.config.json`
- Environment variables: `MEM0_*` → `NINAIVALAIGAL_*`
- Updated database connection strings
- JWT secret key variables updated

#### MCP Server
- Server name: "mem0" → "ninaivalaigal"
- Resource URIs: `mem0://` → `ninaivalaigal://`
- Updated MCP client configuration
- User ID environment: `MEM0_USER_ID` → `NINAIVALAIGAL_USER_ID`

#### Documentation
- Updated README.md with new brand identity
- Rebranded IDE testing guides
- All command references: `@mem0` → `@e^M`
- Created comprehensive rebranding completion report

#### Architecture Preserved
- FastAPI Server (port 13370) - REST API with JWT auth
- MCP Server (stdio) - Model Context Protocol for AI integration
- Dual-server architecture maintained
- All existing functionality preserved
- Database schema unchanged
- No data loss during transition

#### Migration Support
- Backward compatibility during transition
- Migration guide for existing users
- Environment variable mapping documented
- Configuration file transition support

---

## [2025-09-10] - VS Code Extension Context Isolation Fix

### Fixed
- **VS Code Extension Activation**: Fixed extension not activating due to incompatible activation events and TypeScript version conflicts
- **Context Isolation**: Extension now properly isolates memories by context when using `@e^M recall <context-name>`
- **Debug Output**: Added comprehensive debug logging showing CLI command execution, working directory, project context, exit codes, and raw/formatted output
- **TypeScript Compatibility**: Fixed @types/vscode version mismatch with VS Code engine requirements

### Added
- **Popup Notifications**: Added visible activation notifications for debugging extension loading
- **Context Commands**: Support for `@e^M context start <context-name>` to switch active context
- **Enhanced CLI Integration**: Improved command argument construction for proper context filtering

### Changed
- **Activation Event**: Changed from `onChatParticipant:ninaivalaigal` to `onStartupFinished` for better reliability
- **VS Code Engine**: Lowered minimum VS Code version requirement to 1.74.0
- **Server Port**: Updated to use port 13370 to avoid conflicts with other applications

### Technical Details
- Extension now properly detects workspace folder as default context
- CLI commands correctly constructed with `--context` flags
- Debug output shows complete command execution pipeline
- Context switching works for both recall and remember operations
- All changes properly packaged and version controlled

### Testing Verified
- Extension activation with popup notifications ✅
- Context isolation (`@e^M recall CIP-analysis`) ✅  
- Debug output visibility ✅
- Context switching (`@e^M context start CIP-analysis`) ✅
- CLI integration and command construction ✅
