<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type, X-API-Key');

include("../autoload.php");

// Rate limiting beállítások
$rateLimitFile = __DIR__ . '/rate_limit.json';
$rateLimitWindow = 3600; // 1 óra
$maxRequests = 100; // Maximum kérések száma ablakban

// API kulcs ellenőrzése
$validApiKeys = [
    'your-secure-api-key-here' => [
        'name' => 'Default Client',
        'rate_limit' => 100
    ]
];

$apiKey = $_SERVER['HTTP_X_API_KEY'] ?? null;
if (!$apiKey || !isset($validApiKeys[$apiKey])) {
    http_response_code(401);
    echo json_encode(['error' => 'Érvénytelen API kulcs']);
    exit;
}

// Rate limiting implementáció
function checkRateLimit($apiKey, $rateLimitFile, $window, $maxRequests) {
    $currentTime = time();
    $rateData = [];
    
    if (file_exists($rateLimitFile)) {
        $rateData = json_decode(file_get_contents($rateLimitFile), true);
    }
    
    // Régi bejegyzések törlése
    foreach ($rateData as $key => $data) {
        if ($currentTime - $data['timestamp'] > $window) {
            unset($rateData[$key]);
        }
    }
    
    // Új kérés hozzáadása
    $rateData[] = [
        'api_key' => $apiKey,
        'timestamp' => $currentTime
    ];
    
    // Kérések számának ellenőrzése
    $requestCount = 0;
    foreach ($rateData as $data) {
        if ($data['api_key'] === $apiKey && $currentTime - $data['timestamp'] <= $window) {
            $requestCount++;
        }
    }
    
    file_put_contents($rateLimitFile, json_encode($rateData));
    
    return $requestCount <= $maxRequests;
}

if (!checkRateLimit($apiKey, $rateLimitFile, $rateLimitWindow, $maxRequests)) {
    http_response_code(429);
    echo json_encode(['error' => 'Túl sok kérés. Kérjük várjon.']);
    exit;
}

// Adatok beolvasása (POST vagy GET)
$requestData = [];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $requestData = json_decode(file_get_contents('php://input'), true) ?? [];
} else {
    $requestData = $_GET;
}

// Query paraméterek ellenőrzése
$requiredParams = ['login', 'password', 'taxNumber', 'signKey', 'exchangeKey', 'dateFrom', 'dateTo'];
$missingParams = [];

foreach ($requiredParams as $param) {
    if (!isset($requestData[$param])) {
        $missingParams[] = $param;
    }
}

if (!empty($missingParams)) {
    http_response_code(400);
    echo json_encode([
        'error' => 'Hiányzó paraméterek',
        'missing' => $missingParams
    ]);
    exit;
}

try {
    // Felhasználói adatok összeállítása
    $userData = [
        "login" => $requestData['login'],
        "password" => $requestData['password'],
        "taxNumber" => $requestData['taxNumber'],
        "signKey" => $requestData['signKey'],
        "exchangeKey" => $requestData['exchangeKey']
    ];

    // Szoftver adatok (ezek fixek lehetnek)
    $softwareData = [
        "softwareId" => "123456789123456789",
        "softwareName" => "string",
        "softwareOperation" => "ONLINE_SERVICE",
        "softwareMainVersion" => "string",
        "softwareDevName" => "string",
        "softwareDevContact" => "string",
        "softwareDevCountryCode" => "HU",
        "softwareDevTaxNumber" => "string"
    ];

    $config = new NavOnlineInvoice\Config(NavOnlineInvoice\Config::PROD_URL, $userData, $softwareData);
    $reporter = new NavOnlineInvoice\Reporter($config);

    $invoiceQueryParams = [
        "mandatoryQueryParams" => [
            "invoiceIssueDate" => [
                "dateFrom" => $requestData['dateFrom'],
                "dateTo" => $requestData['dateTo'],
            ],
        ],
    ];

    $page = 1;
    $allInvoices = [];
    $maxPages = 100; // Maximum oldalszám korlátozás

    do {
        $invoiceDigestResult = $reporter->queryInvoiceDigest($invoiceQueryParams, $page, "OUTBOUND");

        if (isset($invoiceDigestResult->invoiceDigest)) {
            foreach ($invoiceDigestResult->invoiceDigest as $invoice) {
                $allInvoices[] = $invoice;
            }
        }

        $availablePages = (int)$invoiceDigestResult->availablePage;
        $page++;
    } while ($page <= $availablePages && $page <= $maxPages);

    // Válasz cache-elése
    $cacheKey = md5(json_encode($requestData));
    $cacheFile = __DIR__ . '/cache/' . $cacheKey . '.json';
    $cacheTime = 300; // 5 perc

    if (!is_dir(__DIR__ . '/cache')) {
        mkdir(__DIR__ . '/cache', 0755, true);
    }

    $response = [
        'success' => true,
        'count' => count($allInvoices),
        'invoices' => $allInvoices,
        'cached' => false
    ];

    // Cache mentése
    file_put_contents($cacheFile, json_encode([
        'data' => $response,
        'timestamp' => time()
    ]));

    echo json_encode($response);

} catch (Exception $ex) {
    http_response_code(500);
    echo json_encode([
        'error' => $ex->getMessage(),
        'type' => get_class($ex)
    ]);
} 