// Template: Diesel model (raw). Placeholders substituted by RustModelGenerator.
use diesel::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Queryable, Selectable, Serialize, Deserialize)]
#[diesel(table_name = crate::schema::__MODEL_SNAKE__)]
#[diesel(check_for_backend(diesel::pg::Pg))]
pub struct __MODEL_NAME__ {
    pub id: i32,
    pub name: String,
    pub price: f64,
}