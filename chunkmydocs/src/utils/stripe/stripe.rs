use crate::utils::configs::stripe_config::Config as StripeConfig;
use crate::utils::db::deadpool_postgres::{Client, Pool};
use reqwest::Client as ReqwestClient;

pub async fn create_stripe_customer(email: &str) -> Result<String, Box<dyn std::error::Error>> {
    let stripe_config = StripeConfig::from_env()?;
    let client = ReqwestClient::new();
    let stripe_response = client
        .post("https://api.stripe.com/v1/customers")
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .form(&[("name", email)])
        .send()
        .await?;

    if !stripe_response.status().is_success() {
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            "Failed to create Stripe customer",
        )));
    }

    let stripe_customer: serde_json::Value = stripe_response.json().await?;
    let stripe_customer_id = stripe_customer["id"]
        .as_str()
        .unwrap_or_default()
        .to_string();
    Ok(stripe_customer_id)
}
pub async fn update_invoice_status(
    stripe_invoice_id: &str,
    status: &str,
    db_pool: &Pool,
) -> Result<(), Box<dyn std::error::Error>> {
    let client: Client = db_pool.get().await?;
    client
        .execute(
            "UPDATE invoices SET invoice_status = $1 WHERE stripe_invoice_id = $2",
            &[&status, &stripe_invoice_id],
        )
        .await?;
    Ok(())
}
pub async fn create_stripe_setup_intent(
    customer_id: &str,
    stripe_config: &StripeConfig,
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let client = ReqwestClient::new();

    let form_data = vec![
        ("customer", customer_id),
        ("payment_method_types[]", "card"),
        ("usage", "off_session"),
    ];

    let stripe_response = match client
        .post("https://api.stripe.com/v1/setup_intents")
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .form(&form_data)
        .send()
        .await
    {
        Ok(response) => response,
        Err(e) => return Err(Box::new(e)),
    };

    if !stripe_response.status().is_success() {
        let error_message = match stripe_response.text().await {
            Ok(text) => format!("Failed to create Stripe SetupIntent: {}", text),
            Err(_) => "Failed to create Stripe SetupIntent".to_string(),
        };
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            error_message,
        )));
    }

    let setup_intent: serde_json::Value = match stripe_response.json().await {
        Ok(json) => json,
        Err(e) => return Err(Box::new(e)),
    };

    Ok(setup_intent)
}
pub async fn create_customer_session(
    customer_id: &str,
    stripe_config: &StripeConfig,
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let client = ReqwestClient::new();

    let form_data = vec![
        ("customer", customer_id),
        ("components[payment_element][enabled]", "true"),
        (
            "components[payment_element][features][payment_method_redisplay]",
            "enabled",
        ),
        (
            "components[payment_element][features][payment_method_allow_redisplay_filters][]",
            "always",
        ),
        (
            "components[payment_element][features][payment_method_allow_redisplay_filters][]",
            "limited",
        ),
        (
            "components[payment_element][features][payment_method_allow_redisplay_filters][]",
            "unspecified",
        ),
        (
            "components[payment_element][features][payment_method_remove]",
            "enabled",
        ),
        (
            "components[payment_element][features][payment_method_save]",
            "disabled",
        ),
        (
            "components[payment_element][features][payment_method_redisplay_limit]",
            "1",
        ),
        // (
        //     "components[payment_element][features][payment_method_save_usage]",
        //     "off_session",
        // ),
    ];

    let stripe_response = client
        .post("https://api.stripe.com/v1/customer_sessions")
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .form(&form_data)
        .send()
        .await?;

    if !stripe_response.status().is_success() {
        let error_message = stripe_response.text().await?;
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!(
                "Failed to create Stripe Customer Session: {}",
                error_message
            ),
        )));
    }

    let session: serde_json::Value = stripe_response.json().await?;

    Ok(session)
}
pub async fn list_payment_methods(
    customer_id: &str,
    stripe_config: &StripeConfig,
) -> Result<Vec<serde_json::Value>, Box<dyn std::error::Error>> {
    let client = ReqwestClient::new();

    let url = format!(
        "https://api.stripe.com/v1/customers/{}/payment_methods",
        customer_id
    );

    let stripe_response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .send()
        .await?;

    if !stripe_response.status().is_success() {
        let error_message = stripe_response.text().await?;
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("Failed to list payment methods: {}", error_message),
        )));
    }

    let response: serde_json::Value = stripe_response.json().await?;
    let payment_methods = response["data"]
        .as_array()
        .ok_or("No payment methods found")?
        .to_vec();

    Ok(payment_methods)
}

pub async fn delete_payment_method(
    payment_method_id: &str,
    stripe_config: &StripeConfig,
) -> Result<(), Box<dyn std::error::Error>> {
    let client = ReqwestClient::new();

    let url = format!(
        "https://api.stripe.com/v1/payment_methods/{}/detach",
        payment_method_id
    );

    let stripe_response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .send()
        .await?;

    if !stripe_response.status().is_success() {
        let error_message = stripe_response.text().await?;
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("Failed to delete payment method: {}", error_message),
        )));
    }

    Ok(())
}

pub async fn update_payment_method(
    payment_method_id: &str,
    update_data: serde_json::Value,
    stripe_config: &StripeConfig,
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let client = ReqwestClient::new();

    let url = format!(
        "https://api.stripe.com/v1/payment_methods/{}",
        payment_method_id
    );

    let stripe_response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .json(&update_data)
        .send()
        .await?;

    if !stripe_response.status().is_success() {
        let error_message = stripe_response.text().await?;
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("Failed to update payment method: {}", error_message),
        )));
    }

    let updated_payment_method: serde_json::Value = stripe_response.json().await?;

    Ok(updated_payment_method)
}
pub async fn set_default_payment_method(
    customer_id: &str,
    stripe_config: &StripeConfig,
) -> Result<(), Box<dyn std::error::Error>> {
    let client = ReqwestClient::new();

    // First, get all payment methods for the customer
    let list_url = format!(
        "https://api.stripe.com/v1/payment_methods?customer={}&type=card",
        customer_id
    );

    let list_response = client
        .get(&list_url)
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .send()
        .await?;

    if !list_response.status().is_success() {
        let error_message = list_response.text().await?;
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("Failed to list payment methods: {}", error_message),
        )));
    }

    let payment_methods: serde_json::Value = list_response.json().await?;

    // Sort payment methods by created date (descending) and get the most recent one
    let most_recent_payment_method = payment_methods["data"]
        .as_array()
        .and_then(|methods| {
            methods
                .iter()
                .max_by_key(|method| method["created"].as_i64())
        })
        .ok_or_else(|| {
            std::io::Error::new(std::io::ErrorKind::Other, "No payment methods found")
        })?;

    let payment_method_id = most_recent_payment_method["id"].as_str().ok_or_else(|| {
        std::io::Error::new(std::io::ErrorKind::Other, "Invalid payment method ID")
    })?;

    // Set the most recent payment method as default
    let update_url = format!("https://api.stripe.com/v1/customers/{}", customer_id);

    let update_response = client
        .post(&update_url)
        .header("Authorization", format!("Bearer {}", stripe_config.api_key))
        .form(&[(
            "invoice_settings[default_payment_method]",
            payment_method_id,
        )])
        .send()
        .await?;

    if !update_response.status().is_success() {
        let error_message = update_response.text().await?;
        return Err(Box::new(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("Failed to set default payment method: {}", error_message),
        )));
    }

    Ok(())
}
