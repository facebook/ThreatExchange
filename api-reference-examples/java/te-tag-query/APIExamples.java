// Copyright (c) Meta Platforms, Inc. and affiliates.

// ================================================================
// The main reference tooling is com/facebook/threatexchange/TETagQuery.java,
// which is likely most useful. However, this file is a more clear-cut example
// of incorporating the API into your own framework.
//
// Compile with
//
//   javac com/facebook/threatexchange/*.java APIExamples.java
//
// and run with
//
//   java APIExamples
// ================================================================

import com.facebook.threatexchange.Net;
import com.facebook.threatexchange.DescriptorPostParameters;

import java.io.IOException;

public class APIExamples {
  // ----------------------------------------------------------------
  public static void main(String[] args) throws IOException {
    Net.setAppToken("TX_ACCESS_TOKEN");
    submitExample();
    updateExample();
    copyExample();
  }

  // ----------------------------------------------------------------
  private static void submitExample() {
    boolean showURLs = false;
    boolean dryRun = false;
    DescriptorPostParameters postParams = new DescriptorPostParameters();

    postParams.setIndicatorText("dabbad00f00dfeed5ca1ab1ebeefca11ab1ec00e");
    postParams.setIndicatorType("HASH_SHA1");
    postParams.setDescription("testing API-example post");
    postParams.setShareLevel("AMBER");
    postParams.setStatus("NON_MALICIOUS");
    postParams.setPrivacyType("HAS_WHITELIST");
    postParams.setPrivacyMembers("1064060413755420"); // This is the app ID of another test app
    postParams.setTagsToSet("testing_java_post");

    Net.PostResult postResult = Net.submitThreatDescriptor(postParams, showURLs, dryRun);
    if (!postResult.ok) {
      System.err.println(postResult.errorMessage);
      System.exit(1);
    } else {
      System.out.println(postResult.responseMessage);
    }
  }

  // ----------------------------------------------------------------
  private static void updateExample() {
    boolean showURLs = false;
    boolean dryRun = false;
    DescriptorPostParameters postParams = new DescriptorPostParameters();

    postParams.setDescriptorID("2964083130339380"); // ID of the descriptor to be updated

    postParams.setReactionsToAdd("INGESTED,IN_REVIEW");

    Net.PostResult postResult = Net.updateThreatDescriptor(postParams, showURLs, dryRun);
    if (!postResult.ok) {
      System.err.println(postResult.errorMessage);
      System.exit(1);
    } else {
      System.out.println(postResult.responseMessage);
    }
  }

  // ----------------------------------------------------------------
  private static void copyExample() {
    boolean verbose = false;
    boolean showURLs = false;
    boolean dryRun = false;
    DescriptorPostParameters postParams = new DescriptorPostParameters();

    // ID of descriptor to make a copy of. All remaining fields are overrides
    // to that copy-from template.
    postParams.setDescriptorID("2964083130339380");

    // Modifications to the copy-from template are as follows.

    postParams.setDescription("our copies");
    postParams.setIndicatorText("dabbad00f00dfeed5ca1ab1ebeefca11ab1ec0ce");
    postParams.setIndicatorType("HASH_SHA1");

    // This is the ID of a privacy group which includes two test apps.
    //
    // See also
    // https://developers.facebook.com/apps/your-app-id-goes-here/threat-exchange/privacy_groups
    //
    // Note: in the TEAPI at present we can't read the privacy-members of a
    // copy-from descriptor unless we already own it, so this needs to be
    // specified explicitly here.
    postParams.setPrivacyMembers("781588512307315"); // Comma-delimited if there are multiples
    postParams.setPrivacyType("HAS_PRIVACY_GROUP");

    postParams.setTagsToAdd("testing-copy");

    Net.PostResult postResult = Net.copyThreatDescriptor(postParams, verbose, showURLs, dryRun);
    if (!postResult.ok) {
      System.err.println(postResult.errorMessage);
      System.exit(1);
    } else {
      System.out.println(postResult.responseMessage);
    }
  }

}
