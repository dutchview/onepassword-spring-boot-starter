package com.dutchview.onepassword.config;

import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Import;

@AutoConfiguration
@ConditionalOnProperty(prefix = "onepassword-spring-boot", name = "enabled", havingValue = "true", matchIfMissing = true)
@Import({OnePasswordConfigurations.OnePasswordPropertySourceConfiguration.class})
public class OnePasswordAutoConfiguration {

}
