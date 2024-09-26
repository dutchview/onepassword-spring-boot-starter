package com.dutchview.onepassword.model;

import lombok.Data;

@Data
@lombok.ToString(includeFieldNames = true)
public class Vault {
    String id;
    Integer attributeVersion;
    Integer contentVersion;
    String createdAt;
    Integer items;
    String name;
    String type;
    String updatedAt;
}
