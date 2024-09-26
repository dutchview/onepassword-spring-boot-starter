package com.dutchview.onepassword.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.Collection;

@ConfigurationProperties(prefix = "onepassword-spring-boot")
public class OnePasswordProperties {
    boolean enabled;
    String url;
    String apiToken;
    Collection<String> vaultNames;
}