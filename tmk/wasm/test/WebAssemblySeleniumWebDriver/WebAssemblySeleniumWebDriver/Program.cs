// See https://aka.ms/new-console-template for more information
//create object of chrome options
using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;
using OpenQA.Selenium.Firefox;
using WebAssemblySeleniumWebDriver.Services;
using WebDriverManager;
using WebDriverManager.DriverConfigs.Impl;

Boolean runInChrome = true;
Boolean isTMK = true;
String csvFilePath = String.Empty;
String siteUrl = String.Empty;
String downloadFilePath = String.Empty;

// Check if command line arguments are passed.
if (args == null || args.Length < 1) {
    Console.WriteLine("Please pass all the required command line arguments");
    return;
}

runInChrome = args[0].ToLower() == "chrome";
isTMK = args[1].ToLower() == "tmk";

// Validate if all required parameters are passed.
if (isTMK && args?.Length < 4) {
    Console.WriteLine("Please pass all the required command line arguments");
    return;
}

csvFilePath = args!=null ? args[2] : "";

if (isTMK) {
    downloadFilePath = args != null ? args[3] : "";
    siteUrl = args?.Length > 4 ? args[4] : "http://localhost:9093";
}

// Verify if a proper download path is passed for downloading generated TMK files during video hashing.
if (isTMK && (string.IsNullOrWhiteSpace(downloadFilePath) || !Directory.Exists(downloadFilePath))) {
    Console.WriteLine("Please pass in a valid Directory path for downloading the TMK files.");
    return;
}

try {

    IWebDriver driver;

    if (runInChrome) {
        new DriverManager().SetUpDriver(new ChromeConfig());
        ChromeOptions options = new ChromeOptions();
        // Set the options to run chrome browser in headless mode . For both PDQ and TMK hash testing we will be running browser in
        // headless mode.
        options.AddArguments("headless");
        // Set the below options if we are running TMK hash comparison.
        if (isTMK) {
            options.AddUserProfilePreference("download.default_directory",downloadFilePath);
            options.AddUserProfilePreference("disable-popup-blocking","true");
            options.AddUserProfilePreference("profile.default_content_setting_values.automatic_downloads",1);
        }
        driver = new ChromeDriver(options);
    }
    else {
        //new DriverManager().SetUpDriver(new FirefoxConfig());
        FirefoxOptions options = new FirefoxOptions();
        // Set the options to run chrome browser in headless mode . For both PDQ and TMK hash testing we will be running browser in
        // headless mode.
        options.AddArguments("--headless");

        // Set the below options if we are running TMK hash comparison.
        if (isTMK) {
            options.SetPreference("browser.download.folderList",2);
            options.SetPreference("browser.download.dir",downloadFilePath);
            options.SetPreference("browser.helperApps.neverAsk.saveToDisk","video/tmk");
            options.SetPreference("pdfjs.enabledCache.state",false);
        }
        driver = new FirefoxDriver($"{Environment.CurrentDirectory}/Resources/Drivers/Firefox",options);
    }

    if (isTMK) {
        TMKHashing.GetHash(driver,csvFilePath,siteUrl,downloadFilePath);
    }
    else {
        Console.WriteLine("Please verify all the command line arguments are passed properly.");
    }

    // Quits the driver instance to close the webdriver session
    driver.Quit();
}
catch (Exception ex) {
    Console.WriteLine($"Error occured while executing program execution. Error Message : {ex.Message}");
}
