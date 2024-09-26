# OnePassword Spring Boot Starter - Auto Configuration

## Overview

This project is a Spring Boot Starter for automatically retrieving secrets stored in [1Password](https://1password.com/) and making them available as properties in your Spring Boot application. It simplifies the integration with the 1Password API, allowing for seamless secret management without hardcoding sensitive data in your configuration files.

## Features
- Automatically retrieves secrets from 1Password vaults.
- Makes secrets available as Spring properties.
- Configurable using `application.properties` or `application.yml`.
- Supports multiple vaults.

## Prerequisites

- Java 8 or higher
- Spring Boot 2.5 or higher
- A valid 1Password account and API token

## Getting Started

### 1. Add the Dependency

To use this starter in your Spring Boot project, add the following dependency to your `pom.xml`:

```xml
<repositories>
  <repository>
    <id>jitpack.io</id>
    <url>https://jitpack.io</url>
  </repository>
</repositories>

<dependency>
  <groupId>com.github.dutchview</groupId>
  <artifactId>onepassword-spring-boot-starter</artifactId>
  <version>1.0.7</version>
  <classifier>plain</classifier>
</dependency>
```

or for gradle:

```
repositories {
    mavenCentral()
    maven { url "https://jitpack.io"  }
}

dependencies {
    implementation 'com.github.dutchview:onepassword-spring-boot-starter:1.0.8:plain'
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

**Note**: If you configure properties both in the application.properties or application.yml files, keep in mind that properties in application.yml take precedence. Be sure to avoid conflicts between these configurations to ensure expected behavior.

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


# Deployment Instructions for `onepassword-spring-boot-starter`

This guide provides steps to deploy a new version of the `onepassword-spring-boot-starter` tool using **GitHub** and **JitPack**, since we were unable to use GitHub Packages to deploy a Maven package that is publicly reachable. We now rely on JitPack for package distribution.

## Prerequisites

- Ensure you have a **GitHub account** with push access to the repository.
- Make sure your local Git environment is properly set up with the latest version of the tool.

## Steps to Deploy a New Version

### 1. **Push a New Version to GitHub**

1. Make sure your project is up to date with the latest changes.

2. Bump the version in your `build.gradle` (if using Gradle) or `pom.xml` (if using Maven). For example:

  - In `build.gradle`:
    ```groovy
    version = '1.0.7' // Update version here
    ```

3. Commit and push the changes to the main branch (or another branch if using pull requests).

   ```bash
   git add .
   git commit -m "Bump version to 1.0.7"
   git push origin main
   ```

### 2. **Tag the New Version**

After pushing the changes, tag the new version in Git:

1. Create a new tag with the version number:
   ```bash
   git tag 1.0.7
   ```

2. Push the tag to GitHub:
   ```bash
   git push origin 1.0.7
   ```

### 3. **Create a GitHub Release**

To make the release official and accessible via JitPack, you need to create a **GitHub Release** associated with the new tag:

1. Go to your repository on GitHub (e.g., `https://github.com/dutchview/onepassword-spring-boot-starter`).

2. Click on the **Releases** tab (found near the top of the repository page).

3. Click the **Draft a new release** button.

4. Fill in the following details:
  - **Tag version**: Select the tag you just pushed (e.g., `1.0.7`).
  - **Release title**: Name the release (e.g., `1.0.7`).
  - **Description**: Add any release notes (e.g., new features, bug fixes).

5. Optionally, you can attach binaries (if necessary) by uploading any relevant files.

6. Click **Publish Release**.

### 4. **Verify JitPack Build**

Once the GitHub release is created, JitPack will automatically detect it and attempt to build the project. To verify:

1. Visit the JitPack page for your repository:
  - Example: `https://jitpack.io/#dutchview/onepassword-spring-boot-starter`

2. Check if the new version appears under "Releases". You should see the new version (e.g., `1.0.7`) and its build status.

3. If there are any build errors, review them and fix any issues in the project configuration. Push fixes and re-tag/release if necessary.

### Reference Links

- [JitPack Documentation](https://jitpack.io/#dutchview/onepassword-spring-boot-starter)
- [GitHub Release Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)

---

By following the steps above, you will successfully deploy a new version of the tool, ensuring that users can access it via JitPack.

## License

This project is licensed under the MIT License.

## Contributing

Feel free to submit issues, fork the repository, and send pull requests! We appreciate your feedback and contributions to improving this starter.

## Contact

If you have any questions or need further assistance, feel free to contact us at support@dutchview.com.

---

This README provides a developer-oriented guide to integrating 1Password with Spring Boot through this starter. Follow the steps above to easily retrieve and manage your secrets securely in your Spring Boot application.