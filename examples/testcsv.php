<?php
// lekérdezés tól ig 
include ("config.php");
include("utilka.php");

$wKezd=$argv[1];
$wVege=utolsoNap($argv[1]);


try {
    $config = new NavOnlineInvoice\Config($apiUrl, $userData, $softwareData);
    $reporter = new NavOnlineInvoice\Reporter($config);
    
    $invoiceQueryParams = [
        "mandatoryQueryParams" => [
            "invoiceIssueDate" => [
                "dateFrom" => $wKezd,
                "dateTo" => $wVege
            ]
        ]
    ];
    $irany='OUTBOUND';
$delimiter= ";" ;
// $irany='INBOUND';
    $invoiceDigestResult = $reporter->queryInvoiceDigest($invoiceQueryParams, 1, $irany);
    
    // ennyi oldalt kell lapoznom
    $WinvoiceDigestResult = $invoiceDigestResult->availablePage;
    
    
    for ($x = 1; $x <= $WinvoiceDigestResult; $x ++) {
        
        $invoiceDigestResult = $reporter->queryInvoiceDigest($invoiceQueryParams, $x, $irany);
        
        // foreach($invoiceDigestResult -> children() as $val)
        // foreach($invoiceDigestResult as $val){
        foreach ($invoiceDigestResult->invoiceDigest as $val) {
            //echo "'"; 
    echo $val->invoiceNumber . $delimiter  ;
            echo $val->customerName .  $delimiter  ;
            echo $val->customerTaxNumber .  $delimiter  ;
            echo $val->index .  $delimiter  ;
            echo $val->insDate .  $delimiter  ;
            echo $val->invoiceDeliveryDate .  $delimiter  ;
            echo $val->invoiceIssueDate . $delimiter  ;
            echo $val->invoiceNetAmountHUF .  $delimiter  ;
            echo $val->invoiceVatAmountHUF .  $delimiter  ;
            echo $val->paymentMethod . $delimiter  ;
            echo $val->paymentDate .  $delimiter  ;
            echo $val->supplierName .  $delimiter  ;
            echo $val->supplierTaxNumber .  $delimiter  ;
            echo $val->transactionId .  $delimiter  ;
$statusXml = $reporter->queryTransactionStatus($val->transactionId);
echo $statusXml->processingResults->processingResult->invoiceStatus  .  $delimiter  ;
echo $statusXml->processingResults->processingResult-> businessValidationMessages -> validationResultCode .  $delimiter  ;
echo $statusXml->processingResults->processingResult-> businessValidationMessages -> validationErrorCode . $delimiter  ;
echo $statusXml->processingResults->processingResult-> businessValidationMessages -> message .  PHP_EOL ;

        }
    }
} catch (Exception $ex) {
    print get_class($ex) . ": " . $ex->getMessage();
}

?>