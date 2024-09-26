package com.dutchview.onepassword.model;

import lombok.Data;

import java.util.List;

@Data
@lombok.ToString(includeFieldNames = true)
public class ItemDetails {
    String id;
    String category;
    String createdAt;
    List<Field> fields;
    String lastEditedBy;
    List<Section> sections;
    String title;
    String updatedAt;
    Vault vault;
    Integer version;

    @Data
    @lombok.ToString(includeFieldNames = true)
    public static class Field {
        String id;
        String label;
        String purpose;
        String type;
        String value;
        Section section;
    }

    @Data
    @lombok.ToString(includeFieldNames = true)
    public static class Section {
        String id;
    }
}