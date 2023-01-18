// Copyright (c) Meta Platforms, Inc. and affiliates.

// See https://aka.ms/new-console-template for more information
//create object of chrome options
using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;
using OpenQA.Selenium.Firefox;
using WebAssemblySeleniumWebDriver.Services;
using WebDriverManager;
using WebDriverManager.DriverConfigs.Impl;

Boolean runInChrome = true;
Boolean isPDQMD5 = true;
String csvFilePath = String.Empty;
String siteUrl = String.Empty;

// Check if command line arguments are passed.
if (args == null || args.Length < 1) {
    Console.WriteLine("Please pass all the required command line arguments");
    return;
}

runInChrome = args[0].ToLower() == "chrome";
isPDQMD5 = args[1].ToLower() == "pdqmd5";

// Validate if all required parameters are passed.
if ((isPDQMD5 && args?.Length < 3) || (!isPDQMD5 && args?.Length < 4)) {
    Console.WriteLine("Please pass all the required command line arguments");
    return;
}

csvFilePath = args!=null ? args[2]:"";

if (isPDQMD5) {
    siteUrl = args?.Length > 3 ? args[3] : "http://localhost:9093";
}

try {

    IWebDriver driver;

    if (runInChrome) {
        new DriverManager().SetUpDriver(new ChromeConfig());
        ChromeOptions options = new ChromeOptions();
        // Set the options to run chrome browser in headless mode . For both PDQ and TMK hash testing we will be running browser in
        // headless mode.
        options.AddArguments("headless");
        driver = new ChromeDriver(options);
    }
    else {
        //new DriverManager().SetUpDriver(new FirefoxConfig());
        FirefoxOptions options = new FirefoxOptions();
        // Set the options to run chrome browser in headless mode . For both PDQ and TMK hash testing we will be running browser in
        // headless mode.
        options.AddArguments("--headless");
        driver = new FirefoxDriver($"{Environment.CurrentDirectory}/Resources/Drivers/Firefox",options);
    }

    if (isPDQMD5) {
        PDQMD5Hashing.GetHash(driver,csvFilePath,siteUrl);        
    }
    else {
        Console.WriteLine("Please verify the command line arguments values are passed in correctly.");
    }

    // Quits the driver instance to close the webdriver session
    driver.Quit();

}
catch (Exception ex) {
    Console.WriteLine($"Error occured while executing program execution. Error Message : {ex.Message}");
}
