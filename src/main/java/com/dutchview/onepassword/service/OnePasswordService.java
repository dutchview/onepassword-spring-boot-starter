package com.dutchview.onepassword.service;

import com.dutchview.onepassword.model.Item;
import com.dutchview.onepassword.model.ItemDetails;
import com.dutchview.onepassword.model.Vault;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestTemplate;

import java.util.List;

public class OnePasswordService {
    private final String connectApiUrl;
    private final String apiToken;
    private final RestTemplate restTemplate;

    public OnePasswordService(
            String apiUrl,
            String apiToken,
            RestTemplateBuilder restTemplateBuilder) {
        this.restTemplate = restTemplateBuilder.build();
        this.connectApiUrl = apiUrl;
        this.apiToken = apiToken;
    }

    /**
     * Get vault by UUID
     *
     * @param vaultUuid UUID of the vault
     * @return Vault object
     */
    public Vault getVaultById(String vaultUuid) {
            return restTemplate.exchange(
                    connectApiUrl + "/v1/vaults/" + vaultUuid,
                    HttpMethod.GET,
                    new HttpEntity<>(getHeaders()),
                    Vault.class).getBody();
    }

    /**
     * Get all vaults
     * @return List of vaults
     * @see Vault
     */
    public List<Vault> getVaults() {
        return restTemplate.exchange(
                connectApiUrl + "/v1/vaults",
                HttpMethod.GET,
                new HttpEntity<>(getHeaders()),
                new ParameterizedTypeReference<List<Vault>>() {}).getBody();
    }

    /**
     * Get all vaults
     * @return List of vaults
     * @see Vault
     */
    public Vault vaultByName(String name) {
        return getVaults().stream()
                .filter(vault -> vault.getName().equals(name))
                .findFirst()
                .orElse(null);
    }

    public List<Item> listItems(String vaultUuid) {
        return restTemplate.exchange(
                connectApiUrl + "/v1/vaults/" + vaultUuid + "/items",
                HttpMethod.GET,
                new HttpEntity<>(getHeaders()),
                new ParameterizedTypeReference<List<Item>>() {}).getBody();
    }

    public ItemDetails listItemDetails(String vaultUuid, String itemId) {
        return restTemplate.exchange(
                connectApiUrl + "/v1/vaults/" + vaultUuid + "/items/" + itemId,
                HttpMethod.GET,
                new HttpEntity<>(getHeaders()),
                ItemDetails.class).getBody();
    }

    private HttpHeaders getHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(apiToken);
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }
}
