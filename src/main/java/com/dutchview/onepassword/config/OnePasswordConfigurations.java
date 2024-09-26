package com.dutchview.onepassword.config;

import com.dutchview.onepassword.model.ItemDetails;
import com.dutchview.onepassword.service.OnePasswordService;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.PropertiesPropertySource;

import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

public class OnePasswordConfigurations {

    @Configuration(proxyBeanMethods = false)
    static class OnePasswordPropertySourceConfiguration {
        @Bean(name = "onePasswordPropertySourceConfiguration")
        public PropertySourcesPlaceholderConfigurer onePasswordPropertySourceConfiguration(
                ConfigurableEnvironment environment, ApplicationContext applicationContext) {
            String onePasswordUrl = environment.getProperty("onepassword-spring-boot.url");
            String onePasswordApiToken = environment.getProperty("onepassword-spring-boot.apiToken");
            OnePasswordService onePasswordService = new OnePasswordService(
                    onePasswordUrl,
                    onePasswordApiToken,
                    applicationContext.getBean(RestTemplateBuilder.class));

            // iterate over the vaultNames list
            List<String> vaultNames = new ArrayList<>();
            while (environment.containsProperty("onepassword-spring-boot.vaultNames[" + vaultNames.size() + "]")) {
                vaultNames.add(environment.getProperty("onepassword-spring-boot.vaultNames[" + vaultNames.size() + "]"));
            }

            PropertySourcesPlaceholderConfigurer configurer = new PropertySourcesPlaceholderConfigurer();

            Properties customProperties = new Properties();
            // iterate over the vaultNames list
            onePasswordService.getVaults().stream().filter(vault -> {
                return vaultNames.contains(vault.getName());
            }).forEach(vault -> {
                onePasswordService.listItems(vault.getId()).forEach(item -> {
                    ItemDetails itemDetails = onePasswordService.listItemDetails(vault.getId(), item.getId());
                    itemDetails.getFields().forEach(field -> {
                        if (field.getValue() != null) {
                            customProperties.setProperty(item.getTitle() + "." + field.getLabel(), field.getValue());
                        }
                    });
                });
            });

            PropertiesPropertySource customPropertySource = new PropertiesPropertySource("onepasswordProperties", customProperties);
            environment.getPropertySources().addLast(customPropertySource);
            configurer.setPropertySources(environment.getPropertySources());

            return configurer;
        }
    }
}