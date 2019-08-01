
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.lang.NumberFormatException;
import java.lang.StringBuilder;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.format.DateTimeFormatterBuilder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Stream;

import static java.util.Comparator.comparing;
import static java.util.stream.Collectors.joining;
import static java.util.stream.Collectors.toList;

/**
 * Example technique for retrieving all hashes with a given tag from ThreatExchange.
 * Notes:
 * * We use the tagged_objects endpoint to fetch IDs of all hashes. This endpoint
 *   doesn't return all desired metadata fields, so we use it as a quick map from
 *   tag ID to list of hash IDs. This is relatively quick.
 * * Then for each resulting hash ID we do a query for all fields associated with that
 *   ID. This is relatively slow, but batching multiple IDs per query helps a lot.
 *
 * Examples:
 *   javac TETagQuery.java
 *   java TETagQuery --pdq -q tag-to-details media_type_photo
 *   java TETagQuery --photodna -q tag-to-details media_type_photo
 *   java TETagQuery --md5 tag-to-details media_type_video
 */
public class TETagQuery {
  private static final String PROGNAME = "TETagQuery";
  private static String APP_TOKEN = null;
  private static final String DEFAULT_APP_TOKEN_ENV_NAME = "TX_ACCESS_TOKEN";

  // https://developers.facebook.com/docs/threat-exchange/best-practices#batching
  private static final int MAX_IDS_PER_QUERY = 50;

  private static final String TE_BASE_URL = "https://graph.facebook.com/v3.1";

  // These are all conventions for hash-sharing over ThreatExchange.
  private static final String HASH_TYPE_PHOTODNA = "HASH_PHOTODNA";
  private static final String HASH_TYPE_PDQ = "HASH_PDQ";
  private static final String HASH_TYPE_MD5 = "HASH_MD5";
  private static final String HASH_TYPE_TMK = "HASH_TMK";

  private static final String THREAT_DESCRIPTOR = "THREAT_DESCRIPTOR";

  private static final String TAG_PREFIX_MEDIA_TYPE = "media_type_";
  private static final String TAG_MEDIA_TYPE_PHOTO = "media_type_photo";
  private static final String TAG_MEDIA_TYPE_VIDEO = "media_type_video";
  private static final String TAG_MEDIA_TYPE_LONG_HASH_VIDEO = "media_type_long_hash_video";

  private static final String TAG_PREFIX_MEDIA_PRIORITY = "media_priority_";
  private static final String TAG_MEDIA_PRIORITY_S0 = "media_priority_s0";
  private static final String TAG_MEDIA_PRIORITY_S1 = "media_priority_s1";
  private static final String TAG_MEDIA_PRIORITY_S2 = "media_priority_s2";
  private static final String TAG_MEDIA_PRIORITY_S3 = "media_priority_s3";
  private static final String TAG_MEDIA_PRIORITY_T0 = "media_priority_t0";
  private static final String TAG_MEDIA_PRIORITY_T1 = "media_priority_t1";
  private static final String TAG_MEDIA_PRIORITY_T2 = "media_priority_t2";
  private static final String TAG_MEDIA_PRIORITY_T3 = "media_priority_t3";

  // ================================================================
  // MAIN COMMAND-LINE ENTRY POINT
  // ================================================================

  /**
   * Usage function for main().
   */
  private static void usage(int exitCode) {
    PrintStream o = Utils.getPrintStream(exitCode);
    o.printf("Usage: %s [options] {verb} {verb arguments}\n", PROGNAME);
    o.printf("Downloads photo/video hashes in bulk from ThreatExchange, given\n");
    o.printf("either a tag name or a list of IDs one per line on standard input.\n");
    o.printf("Options:\n");
    o.printf("  -h|--help      Show detailed help.\n");
    o.printf("  --list-verbs   Show a list of supported verbs.\n", PROGNAME);
    o.printf("  --list-tags    Show a list of supported tags.\n", PROGNAME);
    o.printf("  -q|--quiet     Only print IDs/hashes output with no narrative.\n");
    o.printf("  -v|--verbose   Print IDs/hashes output along with narrative.\n");
    o.printf("  -s|--show-urls Print URLs used for queries, before executing them.\n");
    o.printf("  -a|--app-token-env-name {...} Name of app-token environment variable.\n");
    o.printf("                 Defaults to \"%s\".\n", DEFAULT_APP_TOKEN_ENV_NAME);
    CommandHandlerFactory.list(o);
    System.exit(exitCode);
  }

  /**
   * There can be only one.
   */
  public static void main(String[] args) throws IOException {

    // Set defaults
    String appTokenEnvName = DEFAULT_APP_TOKEN_ENV_NAME;
    boolean verbose = true;
    boolean showURLs = false;
    int numIDsPerQuery = MAX_IDS_PER_QUERY;
    HashFormatter hashFormatter = new JSONHashFormatter();

    // Override defaults
    while (args.length > 0 && args[0].startsWith("-")) {
      String option = args[0];
      args = Arrays.copyOfRange(args, 1, args.length);

      if (option.equals("-h") || option.equals("--help")) {
        usage(0);

      } else if (option.equals("-v") || option.equals("--verbose")) {
        verbose = true;

      } else if (option.equals("-q") || option.equals("--quiet")) {
        verbose = false;

      } else if (option.equals("-s") || option.equals("--show-urls")) {
        showURLs = true;

      } else if (option.equals("--list-verbs")) {
        CommandHandlerFactory.list(System.out);
        System.exit(0);

      } else if (option.equals("--list-tags")) {
        System.out.println(TAG_MEDIA_TYPE_PHOTO);
        System.out.println(TAG_MEDIA_TYPE_VIDEO);
        System.out.println(TAG_MEDIA_TYPE_LONG_HASH_VIDEO);
        System.out.println(TAG_MEDIA_PRIORITY_S0);
        System.out.println(TAG_MEDIA_PRIORITY_S1);
        System.out.println(TAG_MEDIA_PRIORITY_S2);
        System.out.println(TAG_MEDIA_PRIORITY_S3);
        System.out.println(TAG_MEDIA_PRIORITY_T0);
        System.out.println(TAG_MEDIA_PRIORITY_T1);
        System.out.println(TAG_MEDIA_PRIORITY_T2);
        System.out.println(TAG_MEDIA_PRIORITY_T3);
        System.exit(0);

      } else if (option.equals("--ids-per-query")) {
        if (args.length < 1) {
          usage(1);
        }
        String svalue = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);
        try {
          numIDsPerQuery = Integer.valueOf(svalue);
        } catch (NumberFormatException e) {
          System.err.printf("%s: could not parse \"%s\" as integer.\n",
            PROGNAME, svalue);
          System.exit(1);
        }
        if (numIDsPerQuery < 1 || numIDsPerQuery > MAX_IDS_PER_QUERY) {
          System.err.printf("%s: num IDs per query must be in the range 1..%d; got %d.\n",
            PROGNAME, MAX_IDS_PER_QUERY, numIDsPerQuery);
          System.exit(1);
        }

      } else if (option.equals("-a") || option.equals("--app-token-env-name")) {
        if (args.length < 1) {
          usage(1);
        }
        appTokenEnvName = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

      } else {
        System.err.printf("%s: unrecognized option \"%s\".\n", PROGNAME, option);
        usage(1);
      }
    }

    setAppToken(appTokenEnvName);

    if (args.length < 1) {
      usage(1);
    }
    String verb = args[0];
    args = Arrays.copyOfRange(args, 1, args.length);

    CommandHandler commandHandler = CommandHandlerFactory.create(verb);
    if (commandHandler == null) {
      System.err.printf("%s: verb \"%s\" not found.\n", PROGNAME, verb);
      System.exit(1);
    }
    commandHandler.handle(args, numIDsPerQuery, verbose, showURLs,
      hashFormatter);
  }

  /**
   * Gets the ThreatExchange app token from an environment variable.
   * Feel free to replace the app-token discovery method here with whatever
   * is most convenient for your project. However, be aware that app tokens
   * are like passwords and shouldn't be stored in the open.
   */
  private static void setAppToken(String appTokenEnvName) {
    String value = System.getenv().get(appTokenEnvName);
    if (value == null) {
      System.out.printf("Must set %s environment variable in format %s.\n",
        appTokenEnvName, "999999999999999|xxxx-xxxxxxxxx-xxxxxxxxxxxx");
      System.exit(1);
    }
    APP_TOKEN = value;
  }

  // ================================================================
  // Command-handlers invoked from main.
  // ================================================================

  /**
   * Maps verb from main to a handler for it.
   */
  public static class CommandHandlerFactory {
    private static final String LOOK_UP_TAG_ID = "look-up-tag-id";
    private static final String TAG_TO_IDS = "tag-to-ids";
    private static final String IDS_TO_DETAILS = "ids-to-details";
    private static final String TAG_TO_DETAILS = "tag-to-details";
    private static final String INCREMENTAL = "incremental";
    private static final String PAGINATE = "paginate";

    public static CommandHandler create(String verb) {
      switch(verb) {
      case LOOK_UP_TAG_ID:
        return new LookUpTagIDHandler(verb);
      case TAG_TO_IDS:
        return new TagToIDsHandler(verb);
      case IDS_TO_DETAILS:
        return new IDsToDetailsHandler(verb);
      case TAG_TO_DETAILS:
        return new TagToDetailsHandler(verb);
      case INCREMENTAL:
        return new IncrementalHandler(verb);
      case PAGINATE:
        return new PaginateHandler(verb);
      default:
        return null;
      }
    }

    public static void list(PrintStream o) {
      o.printf("Verbs:\n");
      o.printf("  %s\n", LOOK_UP_TAG_ID);
      o.printf("  %s\n", TAG_TO_IDS);
      o.printf("  %s\n", IDS_TO_DETAILS);
      o.printf("  %s\n", TAG_TO_DETAILS);
      o.printf("  %s\n", INCREMENTAL);
      o.printf("  %s\n", PAGINATE);
    }
  }

  /**
   * Code-reuse for various command-handlers.
   */
  public static abstract class CommandHandler {
    protected static String _verb;
    public CommandHandler(String verb) {
      _verb = verb;
    }
    abstract void usage(int exitCode);
    abstract void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      HashFormatter hashFormatter
    );
  }

  // ----------------------------------------------------------------
  public static class LookUpTagIDHandler extends CommandHandler {
    public LookUpTagIDHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s {one or more tag names}\n",
        PROGNAME, _verb);
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      HashFormatter hashFormatter
    ) {
      HashFilterer hashFilterer = new AllHashFilterer();

      if (args.length < 1) {
        usage(1);
      }

      for (String tagName : args) {
        String tagID = Net.getTagIDFromName(tagName, showURLs);
        if (tagID == null) {
          System.out.printf("tag_name=%s,tag_id=null\n", tagName);
        } else {
          System.out.printf("tag_name=%s,tag_id=%s\n", tagName, tagID);
        }
      }
    }
  }

  // ----------------------------------------------------------------
  public static class TagToIDsHandler extends CommandHandler {
    public TagToIDsHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options] {tag name}\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--since {x}\n");
      o.printf("--until {x}\n");
      o.printf("--page-size {x}\n");
      o.printf("--hash-type {x}\n");
      o.printf("--no-hash -- Don't print the hash to the terminal\n");
      o.printf("The \"since\" or \"until\" parameter is any supported by ThreatExchange,\n");
      o.printf("e.g. seconds since the epoch.\n");
      o.printf("Hash types:\n");
      HashFiltererFactory.list(o);
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      HashFormatter hashFormatter
    ) {
      HashFilterer hashFilterer = new AllHashFilterer();
      int pageSize = 1000;
      boolean printHashString = true;
      String since = null;
      String until = null;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--since")) {
          if (args.length < 1) {
            usage(1);
          }
          since = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--until")) {
          if (args.length < 1) {
            usage(1);
          }
          until = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--page-size")) {
          if (args.length < 1) {
            usage(1);
          }
          pageSize = Integer.valueOf(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--hash-type")) {
          if (args.length < 1) {
            usage(1);
          }

          hashFilterer = HashFiltererFactory.create(args[0]);
          if (hashFilterer == null) {
            System.err.printf("%s %s: unrecognized hash filter \"%s\".\n",
              PROGNAME, _verb, args[1]);
            usage(1);
          }

          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-hash")) {
          printHashString = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (args.length != 1) {
        usage(1);
      }
      String tagName = args[0];

      String tagID = Net.getTagIDFromName(tagName, showURLs);
      if (tagID == null) {
        System.err.printf("%s: could not find tag by name \"%s\".\n",
          PROGNAME, tagName);
        System.exit(1);
      }

      if (verbose) {
        SimpleJSONWriter w = new SimpleJSONWriter();
        w.add("tag_name", tagName);
        w.add("tag_id", tagID);
        System.out.println(w.format());
        System.out.flush();
      }

      // Returns IDs for all photo hashes. The return from this bulk-query call
      // gives back only ID code, hash text, and the uninformative label
      // "THREAT_DESCRIPTOR". From this we can dive in on each item, though, and
      // query for its details one ID at a time.
      List<String> hashIDs = Net.getHashIDsByTagID(tagID, verbose, showURLs,
        hashFilterer, since, until, pageSize, printHashString);

      if (verbose) {
        SimpleJSONWriter w = new SimpleJSONWriter();
        w.add("hash_count", hashIDs.size());
        System.out.println(w.format());
        System.out.flush();

        int i = 0;
        for (String hashID : hashIDs) {
          w = new SimpleJSONWriter();
          w.add("i", i);
          w.add("hash_id", hashID);
          System.out.println(w.format());
          System.out.flush();
          i++;
        }
      } else {
        for (String hashID : hashIDs) {
          System.out.println(hashID);
          System.out.flush();
        }
      }
    }
  }

  // ----------------------------------------------------------------
  public static class IDsToDetailsHandler extends CommandHandler {
    public IDsToDetailsHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options]\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--no-hash -- Don't print the hash to the terminal\n");
      o.printf("--hash-dir {d} -- Write hashes as {ID}.{extension} files in directory named {d}\n");
      o.printf("Please supply IDs one line at a time on standard input.\n");
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      HashFormatter hashFormatter
    ) {
      boolean printHashString = true;
      String hashDir = null;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--hash-dir")) {
          if (args.length < 1) {
            usage(1);
          }
          hashDir = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-hash")) {
          printHashString = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (hashDir != null) {
        File handle = new File(hashDir);
        boolean ok = handle.exists() || handle.mkdirs();
        if (!ok) {
          System.err.printf("%s: could not create output directory \"%s\"\n",
            PROGNAME, hashDir);
          System.exit(1);
        }
      }

      List<String> hashIDs = new ArrayList<String>();

      BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
      String line;
      int lno = 1;
      try {
        while ((line = reader.readLine()) != null) {
          lno++;
          // In Java, line-terminators already stripped for us
          hashIDs.add(line);
        }
      } catch (IOException e) {
        System.err.printf("Couldn't read line %d of standard input.\n", lno);
        System.exit(1);
      }

      outputDetails(hashIDs, numIDsPerQuery, verbose, showURLs, printHashString,
        hashDir, hashFormatter);
    }
  }

  // ----------------------------------------------------------------
  public static class TagToDetailsHandler extends CommandHandler {
    public TagToDetailsHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options] {tag name}\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--since {x}\n");
      o.printf("--until {x}\n");
      o.printf("--page-size {x}\n");
      o.printf("--hash-type {x}\n");
      o.printf("--no-hash -- Don't print the hash\n");
      o.printf("--hash-dir {d} -- Write hashes as {ID}.{extension} files in directory named {d}\n");
      o.printf("The \"since\" or \"until\" parameter is any supported by ThreatExchange,\n");
      o.printf("e.g. seconds since the epoch.\n");
      o.printf("Hash types:\n");
      HashFiltererFactory.list(o);
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      HashFormatter hashFormatter
    ) {
      HashFilterer hashFilterer = new AllHashFilterer();
      int pageSize = 1000;
      String since = null;
      String until = null;
      boolean printHashString = true;
      String hashDir = null;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--hash-dir")) {
          if (args.length < 1) {
            usage(1);
          }
          hashDir = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--since")) {
          if (args.length < 1) {
            usage(1);
          }
          since = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--until")) {
          if (args.length < 1) {
            usage(1);
          }
          until = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--page-size")) {
          if (args.length < 1) {
            usage(1);
          }
          pageSize = Integer.valueOf(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--hash-type")) {
          if (args.length < 1) {
            usage(1);
          }

          hashFilterer = HashFiltererFactory.create(args[0]);
          if (hashFilterer == null) {
            System.err.printf("%s %s: unrecognized hash filter \"%s\".\n",
              PROGNAME, _verb, args[1]);
            usage(1);
          }

          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-hash")) {
          printHashString = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (args.length != 1) {
        usage(1);
      }
      String tagName = args[0];

      if (hashDir != null) {
        File handle = new File(hashDir);
        boolean ok = handle.exists() || handle.mkdirs();
        if (!ok) {
          System.err.printf("%s: could not create output directory \"%s\"\n",
            PROGNAME, hashDir);
          System.exit(1);
        }
      }

      String tagID = Net.getTagIDFromName(tagName, showURLs);
      if (tagID == null) {
        System.err.printf("%s: could not find tag by name \"%s\".\n",
          PROGNAME, tagName);
        System.exit(1);
      }
      if (verbose) {
        SimpleJSONWriter w = new SimpleJSONWriter();
        w.add("tag_name", tagName);
        w.add("tag_id", tagID);
        System.out.println(w.format());
        System.out.flush();
      }

      // Returns IDs for all photo hashes. The return from this bulk-query call
      // gives back only ID code, hash text, and the uninformative label
      // "THREAT_DESCRIPTOR". From this we can dive in on each item, though, and
      // query for its details one ID at a time.
      List<String> hashIDs = Net.getHashIDsByTagID(tagID, verbose, showURLs,
        hashFilterer, since, until, pageSize, printHashString);

      outputDetails(hashIDs, numIDsPerQuery, verbose, showURLs, printHashString,
        hashDir, hashFormatter);
    }
  }

  /**
   * Print details for each hash ID. Shared code between the tag-to-details
   * and IDs-to-details handlers.
   */
  public static void outputDetails(
    List<String> hashIDs,
    int numIDsPerQuery,
    boolean verbose,
    boolean showURLs,
    boolean printHashString,
    String hashDir,
    HashFormatter hashFormatter)
  {
    List<List<String>> chunks = Utils.chunkify(hashIDs, numIDsPerQuery);

    // Now look up details for each ID.
    for (List<String> chunk: chunks) {
      List<SharedHash> sharedHashes = Net.getInfoForIDs(chunk, verbose, showURLs,
        printHashString);
      for (SharedHash sharedHash : sharedHashes) {

        System.out.println(hashFormatter.format(sharedHash, printHashString));

        if (hashDir != null) {
          String path = hashDir + File.separator + sharedHash.hashID + hashTypeToFileSuffix(sharedHash.hashType);

          try {
            outputHashToFile(sharedHash, path, verbose);
          } catch (FileNotFoundException e) {
            System.err.printf("FileNotFoundException: \"%s\".\n", path);
          } catch (IOException e) {
            System.err.printf("IOException: \"%s\".\n", path);
          }
        }
      }
    }
  }

  public static String hashTypeToFileSuffix(String hashType) {
    String suffix = ".hsh";
    switch (hashType) {
    case HASH_TYPE_PHOTODNA:
      suffix = ".pdna";
      break;
    case HASH_TYPE_PDQ:
      suffix = ".pdq";
      break;
    case HASH_TYPE_MD5:
      suffix = ".md5";
      break;
    case HASH_TYPE_TMK:
      suffix = ".tmk";
      break;
    }
    return suffix;
  }

  public static void outputHashToFile(
    SharedHash sharedHash,
    String path,
    boolean verbose)
      throws FileNotFoundException, IOException
  {
    if (sharedHash.hashType.equals(HASH_TYPE_TMK)) {
      outputTMKHashToFile(sharedHash, path, verbose);
    } else {
      outputNonTMKHashToFile(sharedHash, path, verbose);
    }
  }

  // TMK hashes are binary data with data strucure in the TMK package's
  // tmktypes.h. The string attributes are not 8-bit clean in the
  // ThreatExchange API so the hashValue attribute is stored as base64-encoded,
  // with one caveat: the first 12 bytes (which are ASCII) are stored as
  // such, followed by a pipe delimiter, then the rest of the binary file
  // base64-encdoed. Here we undo that encoding.
  public static void outputTMKHashToFile(
    SharedHash sharedHash,
    String path,
    boolean verbose)
      throws FileNotFoundException, IOException
  {
    FileOutputStream fos = new FileOutputStream(path);
    int hlen = sharedHash.hashValue.length();

    String base64EncodedHash = sharedHash.hashValue;

    byte[] bytes = base64EncodedHash.getBytes();
    byte[] first = Arrays.copyOfRange(bytes, 0, 12);
    byte[] rest = Base64.getDecoder().decode(Arrays.copyOfRange(bytes, 13, hlen));
    fos.write(first);
    fos.write(rest);
    if (verbose) {
      SimpleJSONWriter w = new SimpleJSONWriter();
      w.add("path", path);
      w.add("hash_type", sharedHash.hashType);
      w.add("encoded_length", sharedHash.hashValue.length());
      w.add("binary_length", first.length + rest.length);
      System.out.println(w.format());
      System.out.flush();
    }
    fos.close();
  }

  // Just write PhotoDNA, PDQ, MD5, etc. hash-data to the file contents.
  public static void outputNonTMKHashToFile(
    SharedHash sharedHash,
    String path,
    boolean verbose)
      throws FileNotFoundException, IOException
  {
    FileOutputStream fos = new FileOutputStream(path);

    byte[] bytes = sharedHash.hashValue.getBytes();
    fos.write(bytes);
    if (verbose) {
      SimpleJSONWriter w = new SimpleJSONWriter();
      w.add("path", path);
      w.add("hash_type", sharedHash.hashType);
      w.add("hash_length", sharedHash.hashValue.length());
      System.out.println(w.format());
      System.out.flush();
    }

    fos.close();
  }

  // ----------------------------------------------------------------
  // NOTE: THIS IS KNOWN TO NOT CORRECTLY HANDLE PAGINATION.
  // PLEASE USE TAGGED_OBJECTS WITH TAGGED_SINCE.
  public static class IncrementalHandler extends CommandHandler {
    public IncrementalHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s [options] {tag name}\n",
        PROGNAME, _verb);
      o.printf("Options:\n");
      o.printf("--since {x}\n");
      o.printf("--hash-type {x}\n");
      o.printf("--page-size {x}\n");
      o.printf("The \"since\" parameter is any supported by ThreatExchange,\n");
      o.printf("e.g. seconds since the epoch.\n");
      o.printf("Hash types:\n");
      HashFiltererFactory.list(o);
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      HashFormatter hashFormatter
    ) {
      HashFilterer hashFilterer = new AllHashFilterer();
      int pageSize = 1000;
      String since = null;
      String until = null;
      boolean printHashString = true;

      while (args.length > 0 && args[0].startsWith("-")) {
        String option = args[0];
        args = Arrays.copyOfRange(args, 1, args.length);

        if (option.equals("-h") || option.equals("--help")) {
          usage(0);

        } else if (option.equals("--since")) {
          if (args.length < 1) {
            usage(1);
          }
          since = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--until")) {
          if (args.length < 1) {
            usage(1);
          }
          until = args[0];
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--page-size")) {
          if (args.length < 1) {
            usage(1);
          }
          pageSize = Integer.valueOf(args[0]);
          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--hash-type")) {
          if (args.length < 1) {
            usage(1);
          }

          hashFilterer = HashFiltererFactory.create(args[0]);
          if (hashFilterer == null) {
            System.err.printf("%s %s: unrecognized hash filter \"%s\".\n",
              PROGNAME, _verb, args[1]);
            usage(1);
          }

          args = Arrays.copyOfRange(args, 1, args.length);

        } else if (option.equals("--no-hash")) {
          printHashString = false;

        } else {
          System.err.printf("%s %s: unrecognized option \"%s\".\n",
            PROGNAME, _verb, option);
          usage(1);
        }
      }

      if (since == null) {
        System.err.printf("%s %s: --since is required.\n",
          PROGNAME, _verb);
        usage(1);
      }
      if (args.length != 1) {
        usage(1);
      }
      String tagName = args[0];

      String hashTypeForTE = hashFilterer.getTEName();

      List<SharedHash> sharedHashes = Net.getIncremental(tagName, hashTypeForTE, since,
        pageSize, verbose, showURLs);

      for (SharedHash sharedHash : sharedHashes) {
        System.out.println(hashFormatter.format(sharedHash, printHashString));
      }
    }
  }

  // ----------------------------------------------------------------
  public static class PaginateHandler extends CommandHandler {
    public PaginateHandler(String verb) {
      super(verb);
    }

    @Override
    public void usage(int exitCode) {
      PrintStream o = Utils.getPrintStream(exitCode);
      o.printf("Usage: %s %s {URL}\n", PROGNAME, _verb);
      o.printf("Curls the URL, JSON-dumps the return value's data blob, then curls\n");
      o.printf("the next-page URL and repeats until there are no more pages.\n");
      System.exit(exitCode);
    }

    @Override
    public void handle(
      String[] args,
      int numIDsPerQuery,
      boolean verbose,
      boolean showURLs,
      HashFormatter hashFormatter
    ) {
      if (args.length != 1) {
        usage(1);
      }
      String startURL = args[0];
      String nextURL = startURL;

      int pageIndex = 0;
      do {
        if (showURLs) {
          System.out.println("URL:");
          System.out.println(nextURL);
        }
        try (InputStream response = new URL(nextURL).openConnection().getInputStream()) {

          JSONObject object = (JSONObject) new JSONParser().parse(new InputStreamReader(response));
          JSONArray data = (JSONArray) object.get("data");
          JSONObject paging = (JSONObject) object.get("paging");
          if (paging == null) {
            nextURL = null;
          } else {
            nextURL = (String) paging.get("next");
          }

          System.out.println(data.toString());
          pageIndex++;
        } catch (Exception e) {
          e.printStackTrace(System.err);
          System.exit(1);
        }
      } while (nextURL != null);
    }
  }

  // ================================================================
  // UTILITY METHODS
  // ================================================================

  private static class Utils {

    /**
     * Supports the paradigm that usage-functions should print to stdout and
     * exit 0 when asked for via --help, and print to stderr and exit 1
     * when unacceptable command-line syntax is encountered.
     */
    private static PrintStream getPrintStream(int exitCode) {
      return exitCode == 0
        ? System.out
        : System.err;
    }

    /**
     * Splits a list of strings into chunks of a given max length.
     * General-purpose, but for this application, intended to satisfy
     * the max-IDs-per-request for the ThreatExchange IDs-to-details URL.
     */
    public static List<List<String>> chunkify(List<String> stringList, int numPerChunk) {
      List<List<String>> chunks = new ArrayList<List<String>>();
      int n = stringList.size();
      String[] stringArray = new String[n];
      int k = 0;
      for (String s : stringList) {
        stringArray[k++] = s;
      }

      for (int i = 0; i < n; i += numPerChunk) {
        int j = i + numPerChunk;
        if (j > n) {
          j = n;
        }
        String[] subArray = Arrays.copyOfRange(stringArray, i, j);
        chunks.add(Arrays.asList(subArray));
      }

      return chunks;
    }

  } // class Utils

  // ================================================================
  // HTTP-wrapper methods
  // ================================================================

  private static class Net {

    /**
     * Looks up the internal ID for a given tag.
     */
    public static String getTagIDFromName(String tagName, boolean showURLs) {
      String url = TE_BASE_URL
        + "/threat_tags"
        + "/?access_token=" + APP_TOKEN
        + "&text=" + java.net.URLEncoder.encode(tagName); // since user-supplied string
      if (showURLs) {
        System.out.println("URL:");
        System.out.println(url);
      }
      try (InputStream response = new URL(url).openConnection().getInputStream()) {

        // The lookup will get everything that has this as a prefix.
        // So we need to filter the results. This loop also handles the
        // case when the results array is empty.

        // Example: when querying for "media_type_video", we want the 2nd one:
        // { "data": [
        //   { "id": "9999338563303771", "text": "media_type_video_long_hash" },
        //   { "id": "9999474908560728", "text": "media_type_video" },
        //   { "id": "9889872714202918", "text": "media_type_video_hash_long" }
        //   ], ...
        // }

        JSONObject object = (JSONObject) new JSONParser().parse(new InputStreamReader(response));
        JSONArray idAndTextArray = (JSONArray) object.get("data");

        for (Object idAndTextObj : idAndTextArray) {
          JSONObject idAndText = (JSONObject)idAndTextObj;
          String id = (String)idAndText.get("id");
          String text = (String)idAndText.get("text");
          if (text != null && text.equals(tagName)) {
            return id;
          }
        }
        return null;
      } catch (Exception e) {
        e.printStackTrace(System.err);
        System.exit(1);
      }
      return null;
    }

    /**
     * Looks up all descriptors with a given tag. Returns only the IDs. Details must be
     * sought one ID at a time.
     */
    public static List<String> getHashIDsByTagID(
      String tagID,
      boolean verbose,
      boolean showURLs,
      HashFilterer hashFilterer,
      String since, // maybe null
      String until, // maybe null
      int pageSize,
      boolean printHashString
    ) {
      List<String> hashIDs = new ArrayList<String>();

      String pageLimit = Integer.toString(pageSize);
      String startURL = TE_BASE_URL
        + "/" + tagID + "/tagged_objects"
        + "/?access_token=" + APP_TOKEN
        + "&limit=" + pageLimit;
      if (since != null) {
        startURL += "&tagged_since=" + since;
      }
      if (until != null) {
        startURL += "&tagged_until=" + until;
      }

      String nextURL = startURL;

      int pageIndex = 0;
      do {
        if (showURLs) {
          System.out.println("URL:");
          System.out.println(nextURL);
        }
        try (InputStream response = new URL(nextURL).openConnection().getInputStream()) {

          // Format we're parsing:
          // {
          //   "data": [
          //     {
          //       "id": "9915337796604770",
          //       "type": "THREAT_DESCRIPTOR",
          //       "name": "7ef5...aa97"
          //     }
          //     ...
          //   ],
          //   "paging": {
          //     "cursors": {
          //       "before": "XYZIU...NjQ0h3Unh3",
          //       "after": "XYZIUk...FXNzVNd1Jn"
          //     },
          //     "next": "https://graph.facebook.com/v3.1/9999338387644295/tagged_objects?access_token=..."
          //   }
          // }

          JSONObject object = (JSONObject) new JSONParser().parse(new InputStreamReader(response));
          JSONArray data = (JSONArray) object.get("data");
          JSONObject paging = (JSONObject) object.get("paging");
          if (paging == null) {
            nextURL = null;
          } else {
            nextURL = (String) paging.get("next");
          }

          int numItems = data.size();
          if (verbose) {
            SimpleJSONWriter w = new SimpleJSONWriter();
            w.add("page_index", pageIndex);
            w.add("num_items", numItems);
            System.out.println(w.format());
            System.out.flush();
          }

          for (int i = 0; i < numItems; i++) {
            JSONObject item = (JSONObject) data.get(i);

            String itemID = (String) item.get("id");
            String itemType = (String) item.get("type");
            String itemText = (String) item.get("name");
            if (!itemType.equals(THREAT_DESCRIPTOR)) {
              continue;
            }
            if (!hashFilterer.accept(itemText)) {
              continue;
            }

            if (verbose) {
              SimpleJSONWriter w = new SimpleJSONWriter();
              w.add("id", itemID);
              w.add("type", itemType);
              if (printHashString) {
                w.add("hash", itemText);
              }

              System.out.println(w.format());
              System.out.flush();
            }
            hashIDs.add(itemID);
          }

          pageIndex++;
        } catch (Exception e) {
          e.printStackTrace(System.err);
          System.exit(1);
        }
      } while (nextURL != null);
      return hashIDs;
    }

    /**
     * Looks up all metadata for given ID.
     */
    public static List<SharedHash> getInfoForIDs(
      List<String> hashIDs,
      boolean verbose,
      boolean showURLs,
      boolean printHashString
    ) {

      // Check well-formattedness of hash IDs (which may have come from
      // arbitrary data on stdin).
      for(String hashID : hashIDs) {
        try {
          Long.valueOf(hashID);
        } catch (NumberFormatException e) {
          System.err.printf("Malformed hash ID \"%s\"\n", hashID);
          System.exit(1);
        }
      }

      String url = TE_BASE_URL
        + "/?access_token=" + APP_TOKEN
        + "&ids=%5B" + String.join(",", hashIDs) + "%5D"
        + "&fields=raw_indicator,type,added_on,confidence,owner,review_status,severity,share_level,tags";
      if (showURLs) {
        System.out.println("URL:");
        System.out.println(url);
      }

      List<SharedHash> sharedHashes = new ArrayList<SharedHash>();
      try (InputStream response = new URL(url).openConnection().getInputStream()) {
        // {
        //    "990927953l366387": {
        //       "raw_indicator": "87f4b261064696075fffceee39471952",
        //       "type": "HASH_MD5",
        //       "added_on": "2018-03-21T18:47:23+0000",
        //       "confidence": 100,
        //       "owner": {
        //          "id": "788842735455502",
        //          "email": "contactemail\u0040companyname.com",
        //          "name": "Name of App"
        //       },
        //       "review_status": "REVIEWED_AUTOMATICALLY",
        //       "severity": "WARNING",
        //       "share_level": "AMBER",
        //       "tags": {
        //          "data": [
        //             {
        //                "id": "8995447960580728",
        //                "text": "media_type_video"
        //             },
        //             {
        //                "id": "6000177b99449380",
        //                "text": "media_priority_test"
        //             }
        //          ]
        //       },
        //       "id": "4019972332766623"
        //    },
        //    ...
        //  }

        JSONObject outer = (JSONObject) new JSONParser().parse(new InputStreamReader(response));

        for (Iterator iterator = outer.keySet().iterator(); iterator.hasNext();) {
          String key = (String) iterator.next();
          JSONObject item = (JSONObject) outer.get(key);

          if (verbose) {
            System.out.println(item.toString());
          }

          JSONObject owner = (JSONObject)item.get("owner");
          JSONObject tags = (JSONObject)item.get("tags");
          JSONArray tag_data = (JSONArray)tags.get("data");
          int n = tag_data.size();
          String mediaType = "not_found";
          String mediaPriority = "not_found";
          int numMediaType = 0;
          int numMediaPriority = 0;
          for (int j = 0; j < n; j++) {
            JSONObject tag = (JSONObject) tag_data.get(j);
            String tag_text = (String)tag.get("text");
            if (tag_text.startsWith(TAG_PREFIX_MEDIA_TYPE)) {
              mediaType = tag_text.replace(TAG_PREFIX_MEDIA_TYPE, "").toUpperCase();
              numMediaType++;
            } else if (tag_text.startsWith(TAG_PREFIX_MEDIA_PRIORITY)) {
              mediaPriority = tag_text.replace(TAG_PREFIX_MEDIA_PRIORITY, "").toUpperCase();
              numMediaPriority++;
            }
          }

          if (verbose) {
            if (numMediaType != 1 || numMediaPriority != 1) {
              SimpleJSONWriter w = new SimpleJSONWriter();
              w.add("hash_id", (String)item.get("id"));
              w.add("num_media_type", numMediaType);
              w.add("num_media_priority", numMediaPriority);
              System.out.println(w.format());
            }
          }

          SharedHash sharedHash = new SharedHash(
            (String)item.get("id"),
            (String)item.get("raw_indicator"),
            (String)item.get("type"),
            (String)item.get("added_on"),
            Long.toString((Long)item.get("confidence")),
            (String)owner.get("id"),
            (String)owner.get("email"),
            (String)owner.get("name"),
            mediaType,
            mediaPriority);

          sharedHashes.add(sharedHash);
        }
      } catch (Exception e) {
        e.printStackTrace(System.err);
        System.exit(1);
      }
      return sharedHashes;
    }

    /**
     * Looks up all descriptors with a given tag (or tag-prefix), optional
     * hash-type filter, and TE 'since' parameter. Warning: often infinite-loopy!
     * There are many queries for which the 'next' paging parameter will remain
     * non-null on every next-page request.
     */
    public static List<SharedHash> getIncremental(
      String tagName,
      String hashType,
      String since,
      int pageSize,
      boolean verbose,
      boolean showURLs
    ) {
      List<SharedHash> sharedHashes = new ArrayList<SharedHash>();

      String pageLimit = Integer.toString(pageSize);
      String startURL = TE_BASE_URL
        + "/threat_descriptors"
        + "/?access_token=" + APP_TOKEN
        + "&fields=raw_indicator,type,added_on,confidence,owner,review_status,severity,share_level,tags"
        + "&limit=" + pageLimit
        + "&tags=" + tagName
        + "&since=" + since;
      if (hashType != null) {
        startURL = startURL + "&type=" + hashType;
      }

      String nextURL = startURL;

      int pageIndex = 0;
      do {
        if (showURLs) {
          System.out.println("URL:");
          System.out.println(nextURL);
        }
        try (InputStream response = new URL(nextURL).openConnection().getInputStream()) {

          // {
          //    "data": [
          //     {
          //        "added_on": "2018-02-15T10:01:38+0000",
          //        "confidence": 50,
          //        "description": "Description goes here",
          //        "id": "9998888887828886",
          //        "indicator": {
          //           "id": "8858889164495553",
          //           "indicator": "0096f7ffffb07f385630008f495b59ff",
          //           "type": "HASH_MD5"
          //        },
          //        "last_updated": "2018-02-15T10:01:39+0000",
          //        "owner": {
          //           "id": "9977777020662433",
          //           "email": "username\u0040companyname.com",
          //           "name": "Name of App"
          //        },
          //        "precision": "UNKNOWN",
          //        "privacy_type": "HAS_PRIVACY_GROUP",
          //        "raw_indicator": "0096f7ffffb07f385630008f495b59ff",
          //        "review_status": "REVIEWED_MANUALLY",
          //        "severity": "WARNING",
          //        "share_level": "AMBER",
          //        "status": "MALICIOUS",
          //        "type": "HASH_MD5"
          //     },
          //    "paging": {
          //       "cursors": {
          //          "before": "MAZDZD",
          //          "after": "MQZDZD"
          //       }
          //    }
          // }

          JSONObject object = (JSONObject) new JSONParser().parse(new InputStreamReader(response));
          JSONArray data = (JSONArray) object.get("data");
          JSONObject paging = (JSONObject) object.get("paging");
          if (paging == null) {
            nextURL = null;
          } else {
            nextURL = (String) paging.get("next");
          }

          int numItems = data.size();
          if (verbose) {
            SimpleJSONWriter w = new SimpleJSONWriter();
            w.add("page_index", pageIndex);
            w.add("num_items", numItems);
            System.out.println(w.format());
            System.out.flush();
          }

          for (int i = 0; i < numItems; i++) {
            JSONObject item = (JSONObject) data.get(i);

            String itemID = (String) item.get("id");
            String itemType = (String) item.get("type");
            String itemText = (String) item.get("raw_indicator");

            if (verbose) {
              SimpleJSONWriter w = new SimpleJSONWriter();
              w.add("id", itemID);
              w.add("type", itemType);
              w.add("hash", itemText);
              System.out.println(w.format());
              System.out.flush();
            }

            JSONObject owner = (JSONObject)item.get("owner");

            JSONObject tags = (JSONObject)item.get("tags");
            JSONArray tag_data = (JSONArray)tags.get("data");
            int n = tag_data.size();
            String mediaType = "not_found";
            String mediaPriority = "not_found";
            int numMediaType = 0;
            int numMediaPriority = 0;
            for (int j = 0; j < n; j++) {
              JSONObject tag = (JSONObject) tag_data.get(j);
              String tag_text = (String)tag.get("text");
              if (tag_text.startsWith(TAG_PREFIX_MEDIA_TYPE)) {
                mediaType = tag_text.replace(TAG_PREFIX_MEDIA_TYPE, "").toUpperCase();
                numMediaType++;
              } else if (tag_text.startsWith(TAG_PREFIX_MEDIA_PRIORITY)) {
                mediaPriority = tag_text.replace(TAG_PREFIX_MEDIA_PRIORITY, "").toUpperCase();
                numMediaPriority++;
              }
            }

            SharedHash sharedHash = new SharedHash(
              itemID,
              itemText,
              itemType,
              (String)item.get("added_on"),
              Long.toString((Long)item.get("confidence")),
              (String)owner.get("id"),
              (String)owner.get("email"),
              (String)owner.get("name"),
              mediaType,
              mediaPriority);

          }
          pageIndex++;
        } catch (Exception e) {
          e.printStackTrace(System.err);
          System.exit(1);
        }
      } while (nextURL != null);

      return sharedHashes;
    }

  } // Net

  // ================================================================
  // Hash-filterer, using hash-text rather than ThreatExchange 'type'
  // field, since it's far more performant to filter on the former
  // than the latter.
  // ================================================================

  public static class HashFiltererFactory {
    private static final String OPTION_PHOTODNA = "photodna";
    private static final String OPTION_PDQ      = "pdq";
    private static final String OPTION_MD5      = "md5";
    private static final String OPTION_TMK      = "tmk";
    private static final String OPTION_ALL      = "all";

    public static void list(PrintStream o) {
      o.printf("Hash-type filters:\n");
      o.printf("  %s\n", OPTION_PHOTODNA);
      o.printf("  %s\n", OPTION_PDQ);
      o.printf("  %s\n", OPTION_MD5);
      o.printf("  %s\n", OPTION_TMK);
      o.printf("  %s\n", OPTION_ALL);
    }

    public static HashFilterer create(String name) {
      if (name.equals(OPTION_PHOTODNA)) {
        return new PhotoDNAHashFilterer();
      } else if (name.equals(OPTION_PDQ)) {
        return new PDQHashFilterer();
      } else if (name.equals(OPTION_MD5)) {
        return new MD5HashFilterer();
      } else if (name.equals(OPTION_TMK)) {
        return new TMKHashFilterer();
      } else if (name.equals(OPTION_ALL)) {
        return new AllHashFilterer();
      } else {
        return null;
      }
    }
  }

  public interface HashFilterer {
    public abstract boolean accept(String hash);
    public abstract String getTEName();
  }

  /**
   * Filters for any hash-type
   */
  public static class AllHashFilterer implements HashFilterer {
    @Override
    public boolean accept(String hash) {
      return true;
    }
    @Override
    public String getTEName() {
      return null;
    }
  }

  /**
   * Filters ideally for comma-delimited decimal, 144 slots.
   * Only does the minimal check to differentiate from other hash-types
   * we support.
   */
  public static class PhotoDNAHashFilterer implements HashFilterer {
    @Override
    public boolean accept(String hash) {
      if (hash.length() < 287) { // Shortest: 0,0,0,...,0,0,0
        return false;
      }
      return true;
    }
    @Override
    public String getTEName() {
      return "HASH_PHOTODNA";
    }
  }

  /**
   * Filters ideally for 64 hex digits.
   * Only does the minimal check to differentiate from other hash-types
   * we support.
   */
  public static class PDQHashFilterer implements HashFilterer {
    @Override
    public boolean accept(String hash) {
      if (hash.length() != 64) {
        return false;
      }
      return true;
    }
    @Override
    public String getTEName() {
      return "HASH_PDQ";
    }
  }

  /**
   * Filters ideally for 32 hex digits
   * Only does the minimal check to differentiate from other hash-types
   * we support.
   */
  public static class MD5HashFilterer implements HashFilterer {
    @Override
    public boolean accept(String hash) {
      if (hash.length() != 32) {
        return false;
      }
      return true;
    }
    @Override
    public String getTEName() {
      return "HASH_MD5";
    }
  }

  /**
   * Filters ideally for very long (256KB-ish)
   * Only does the minimal check to differentiate from other hash-types
   * we support.
   */
  public static class TMKHashFilterer implements HashFilterer {
    @Override
    public boolean accept(String hash) {
      return hash.length() >= 100000;
    }
    @Override
    public String getTEName() {
      return "HASH_TMK";
    }
  }

  // ================================================================
  // CONTAINER CLASS FOR HASHES AND METADATA
  // ================================================================

  /**
   * Helper container class for parsed results back from ThreatExchange.
   */
  public static class SharedHash {
    public final String hashID;
    public final String hashValue;
    public final String hashType;
    public final String addedOn;
    public final String confidence;
    public final String ownerID;
    public final String ownerEmail;
    public final String ownerName;
    public final String mediaType;
    public final String mediaPriority;

    public SharedHash(
      String hashID_,
      String hashValue_,
      String hashType_,
      String addedOn_,
      String confidence_,
      String ownerID_,
      String ownerEmail_,
      String ownerName_,
      String mediaType_,
      String mediaPriority_
    ) {
      hashID = hashID_;
      hashValue = hashValue_;
      hashType = hashType_;
      addedOn = addedOn_;
      confidence = confidence_;
      ownerID = ownerID_;
      ownerEmail = ownerEmail_;
      ownerName = ownerName_;
      mediaType = mediaType_;
      mediaPriority = mediaPriority_;
    }
  }

  // ================================================================
  // SIMPLE JSON OUTPUT
  // ================================================================
  public static class SimpleJSONWriter {
    LinkedHashMap<String,String> _pairs;

    public SimpleJSONWriter() {
      _pairs = new LinkedHashMap<String,String>();
    }
    public void add(String k, String v) {
      _pairs.put(k, v);
    }
    public void add(String k, int v) {
      _pairs.put(k, Integer.toString(v));
    }
    public String format() {
      StringBuffer sb = new StringBuffer();
      sb.append("{");
      int i = 0;
      for (Map.Entry<String,String> pair : _pairs.entrySet()) {
        if (i > 0) {
          sb.append(",");
        }
        sb.append("\"").append(pair.getKey()).append("\"");
        sb.append(":");
        sb.append("\"").append(pair.getValue()).append("\"");
        i++;
      }
      sb.append("}");
      return sb.toString();
    }
  }

  // ================================================================
  // HASH OUTPUT-FORMATTER
  // ================================================================

  public interface HashFormatter {
    public String format(SharedHash sharedHash, boolean printHashString);
  }

  public static class JSONHashFormatter implements HashFormatter {
    @Override
    public String format(SharedHash sharedHash, boolean printHashString) {
      SimpleJSONWriter w = new SimpleJSONWriter();
      w.add("hash_id", sharedHash.hashID);
      if (printHashString) {
        w.add("hash_value", sharedHash.hashValue);
      }
      w.add("hash_type", sharedHash.hashType);
      w.add("added_on", sharedHash.addedOn);
      w.add("confidence", sharedHash.confidence);
      w.add("owner_id", sharedHash.ownerID);
      w.add("owner_email", sharedHash.ownerEmail);
      w.add("owner_name", sharedHash.ownerName);
      w.add("media_type", sharedHash.mediaType);
      w.add("media_priority", sharedHash.mediaPriority);
      return w.format();
    }
  }

}
