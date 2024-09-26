# OnePassword Spring Boot Starter - Auto Configuration

## Overview

This project is a Spring Boot Starter for automatically retrieving secrets stored in [1Password](https://1password.com/) and making them available as properties in your Spring Boot application. It simplifies the integration with the 1Password API, allowing for seamless secret management without hardcoding sensitive data in your configuration files.

## Features
- Automatically retrieves secrets from 1Password vaults.
- Makes secrets available as Spring properties.
- Configurable using `application.properties` or `application.yml`.
- Supports multiple vaults.

## Prerequisites

- Java 11 or higher
- Spring Boot 2.5 or higher
- A valid 1Password account and API token

## Getting Started

### 1. Add the Dependency

To use this starter in your Spring Boot project, add the following dependency to your `pom.xml`:

```xml
<dependency>
    <groupId>com.dutchview</groupId>
    <artifactId>onepassword-spring-boot-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```
dependencies {
    implementation 'com.dutchview:springboot-onepassword:x.x.x'
}
```


### 2. Configuration

In your `application.yml` or `application.properties`, configure the following properties for the integration:

```yaml
spring:
  application:
    name: demo

onepassword-spring-boot:
  enabled: true
  url: https://1password-connect-api-url
  apiToken: your-api-token
  vaultNames:
    - your-vault-name
```

- **`onepassword-spring-boot.url`**: The API URL for 1Password.
- **`onepassword-spring-boot.apiToken`**: Your 1Password API token (used to authenticate and retrieve secrets).
- **`onepassword-spring-boot.vaultNames`**: List of vaults from which you want to retrieve secrets.

### 3. Secret Management

The retrieved secrets are made available as Spring properties and can be accessed just like any other properties using `@Value` or `Environment`.

For example, if you have a secret in your 1Password vault with the following structure:

- Vault: `edcontrols-development-secrets`
- Item: `database`
    - Field: `username`
    - Field: `password`

You can access these secrets in your application as:

```java
@Value("${database.username}")
private String databaseUsername;

@Value("${database.password}")
private String databasePassword;
```

### 4. Customizing the Configuration

The library allows customization using standard Spring mechanisms. For instance, if you need to add additional configuration properties for your specific use case, you can modify the existing beans or define new ones in your Spring configuration.

### Example Usage

```java
@Configuration
public class MyAppConfig {

    @Value("${database.username}")
    private String username;

    @Value("${database.password}")
    private String password;

    @Bean
    public DataSource dataSource() {
        return DataSourceBuilder.create()
                .username(username)
                .password(password)
                .url("jdbc:mysql://localhost:3306/mydb")
                .build();
    }
}
```

## How It Works

1. **PropertySourcesPlaceholderConfigurer**: The auto-configuration class creates a `PropertySourcesPlaceholderConfigurer` bean that loads properties from 1Password vaults.

2. **1PasswordService**: This service fetches the vaults and item details from the 1Password API. Secrets from selected vaults are processed and added to the environment as properties.

3. **Auto-Configuration**: When the application starts, it automatically retrieves the secrets and injects them into the Spring environment, making them available for use in the application context.


## License

This project is licensed under the MIT License.

## Contributing

Feel free to submit issues, fork the repository, and send pull requests! We appreciate your feedback and contributions to improving this starter.

## Contact

If you have any questions or need further assistance, feel free to contact us at support@dutchview.com.

---

This README provides a developer-oriented guide to integrating 1Password with Spring Boot through this starter. Follow the steps above to easily retrieve and manage your secrets securely in your Spring Boot application.