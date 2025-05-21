<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

require_once __DIR__ . '/../vendor/autoload.php';

// Adalo custom action konfiguráció
$config = [
    'api_key' => 'YOUR_ADALO_API_KEY', // Ezt majd a render.com környezeti változóban tároljuk
    'nav_config' => [
        'apiUrl' => 'https://api-test.onlineszamla.nav.gov.hu/invoiceService',
        'userData' => [
            'login' => 'as3cj8iherbtmtx',
            'password' => 'Sanyika1472',
            'taxNumber' => '32654732',
            'signKey' => '09-8ad7-1e2dbdbea46d4YVJVJWONT9D',
            'exchangeKey' => '7e004YVJVJWOMRAN'
        ],
        'softwareData' => [
            'softwareId' => '123456789123456789',
            'softwareName' => 'string',
            'softwareOperation' => 'LOCAL_SOFTWARE',
            'softwareMainVersion' => 'string',
            'softwareDevName' => 'string',
            'softwareDevContact' => 'string',
            'softwareDevCountryCode' => 'HU',
            'softwareDevTaxNumber' => 'string'
        ]
    ]
];

// API kulcs ellenőrzése
function validateApiKey($apiKey) {
    return $apiKey === $config['api_key'];
}

// Bejövő kérés ellenőrzése
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// API kulcs ellenőrzése
$headers = getallheaders();
$apiKey = $headers['Authorization'] ?? null;

if (!$apiKey || !validateApiKey($apiKey)) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

try {
    // JSON body beolvasása
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input) {
        throw new Exception('Invalid JSON input');
    }

    // Paraméterek kinyerése
    $dateFrom = $input['dateFrom'] ?? null;
    $dateTo = $input['dateTo'] ?? null;
    $direction = $input['direction'] ?? 'OUTBOUND';
    $page = $input['page'] ?? 1;

    if (!$dateFrom || !$dateTo) {
        throw new Exception('A dateFrom és dateTo paraméterek kötelezőek');
    }

    // NAV API konfiguráció
    $navConfig = new NavOnlineInvoice\Config(
        $config['nav_config']['apiUrl'],
        $config['nav_config']['userData'],
        $config['nav_config']['softwareData']
    );
    $reporter = new NavOnlineInvoice\Reporter($navConfig);

    // Lekérdezési paraméterek összeállítása
    $invoiceQueryParams = [
        "mandatoryQueryParams" => [
            "invoiceIssueDate" => [
                "dateFrom" => $dateFrom,
                "dateTo" => $dateTo,
            ],
        ],
    ];

    // Lekérdezés végrehajtása
    $invoiceDigestResult = $reporter->queryInvoiceDigest($invoiceQueryParams, $page, $direction);

    // Válasz formázása
    $response = [
        'success' => true,
        'data' => [
            'currentPage' => (int)$invoiceDigestResult->currentPage,
            'availablePage' => (int)$invoiceDigestResult->availablePage,
            'invoices' => []
        ]
    ];

    // Számlák feldolgozása
    foreach ($invoiceDigestResult->invoiceDigest as $invoice) {
        $response['data']['invoices'][] = [
            'invoiceNumber' => (string)$invoice->invoiceNumber,
            'customerName' => (string)$invoice->customerName,
            'customerTaxNumber' => (string)$invoice->customerTaxNumber,
            'invoiceIssueDate' => (string)$invoice->invoiceIssueDate,
            'invoiceNetAmountHUF' => (float)$invoice->invoiceNetAmountHUF,
            'invoiceVatAmountHUF' => (float)$invoice->invoiceVatAmountHUF,
            'supplierName' => (string)$invoice->supplierName,
            'supplierTaxNumber' => (string)$invoice->supplierTaxNumber,
            'transactionId' => (string)$invoice->transactionId
        ];
    }

    echo json_encode($response, JSON_PRETTY_PRINT);

} catch(Exception $ex) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => $ex->getMessage()
    ], JSON_PRETTY_PRINT);
} 