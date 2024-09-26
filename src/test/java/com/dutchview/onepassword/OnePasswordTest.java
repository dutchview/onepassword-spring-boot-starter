package com.dutchview.onepassword;

import com.dutchview.onepassword.model.Item;
import com.dutchview.onepassword.model.ItemDetails;
import com.dutchview.onepassword.model.Vault;
import com.dutchview.onepassword.service.OnePasswordService;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.web.client.RestTemplateBuilder;

import java.util.List;

@Tag("integration")
@SpringBootTest
class OnePasswordTest {
    @Value("${onepassword-spring-boot.url}") String apiUrl;
    @Value("${onepassword-spring-boot.apiToken}") String apiToken;

    @Test
    public void testGetVaults() {
        List<Vault> vaults = getOnePasswordService().getVaults();
        Assertions.assertTrue(vaults.size() >= 1);
    }

    @Test
    public void testGetVaultById() {
        OnePasswordService onePasswordService = new OnePasswordService(
                apiUrl,
                apiToken,
                new RestTemplateBuilder()
        );

        String vaultUuid = "ilosn7cqafeaghgji27se6ptwu";

        Vault vault = onePasswordService.getVaultById(vaultUuid);
        Assertions.assertEquals("edcontrols-development-secrets", vault.getName());
    }

    @Test
    public void testListItemsId() {
        String vaultUuid = "ilosn7cqafeaghgji27se6ptwu";

        List<Item> items = getOnePasswordService().listItems(vaultUuid);
        Assertions.assertTrue(items.stream().anyMatch(item -> item.getTitle().equals("edcontrols_billing")));
    }

    @Test
    public void testItemDetails() {
        String vaultUuid = "ilosn7cqafeaghgji27se6ptwu";
        String itemId = "6ettj6rtidwp4q43hexu6xaeoy";

        ItemDetails itemDetails = getOnePasswordService().listItemDetails(vaultUuid, itemId);

        Assertions.assertEquals("edcontrols_billing", itemDetails.getTitle());
        ItemDetails.Field theOne = itemDetails.getFields().stream().filter(field -> field.getLabel().equals("superAdminUser")).findFirst().orElseThrow();

        Assertions.assertEquals("data-connectors@edcontrols.com", theOne.getValue());

        theOne = itemDetails.getFields().stream().filter(field -> field.getLabel().equals("superAdminPassword")).findFirst().orElseThrow();
        Assertions.assertEquals("secret 123", theOne.getValue());
    }

    OnePasswordService getOnePasswordService() {
        return new OnePasswordService(
                apiUrl,
                apiToken,
                new RestTemplateBuilder()
        );
    }
}
