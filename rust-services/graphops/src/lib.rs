// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

pub mod db;
pub mod handlers;
pub mod metrics;
pub mod proto {
    pub mod graphops {
        pub mod v1 {
            tonic::include_proto!("ninaivalaigal.graphops.v1");
        }
    }
}
pub mod service;

pub use db::DbPool;
pub use handlers::CypherExecutor;
pub use service::GraphOpsService;
