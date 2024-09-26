package com.dutchview.onepassword.model;

import lombok.Data;

@Data
@lombok.ToString(includeFieldNames = true)
public class Item {
    String id;
    String additionalInformation;
    String category;
    String createdAt;
    String lastEditedBy;
    String title;
    String updatedAt;
    Vault vault;
    Integer version;
}
