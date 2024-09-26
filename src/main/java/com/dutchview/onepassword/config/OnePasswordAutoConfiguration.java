package com.dutchview.onepassword.config;

import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.AutoConfigureBefore;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.autoconfigure.context.PropertyPlaceholderAutoConfiguration;
import org.springframework.context.annotation.Import;

@AutoConfiguration
@AutoConfigureBefore({PropertyPlaceholderAutoConfiguration.class})
@ConditionalOnProperty(prefix = "onepassword-spring-boot", name = "enabled", havingValue = "true", matchIfMissing = true)
@Import({OnePasswordConfigurations.OnePasswordPropertySourceConfiguration.class})
public class OnePasswordAutoConfiguration {

}
