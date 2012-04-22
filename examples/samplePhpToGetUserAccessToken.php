<?php
# requires facebook-php-sdk and is supposed to be in the examples directory
require '../src/facebook.php';

// Create our Application instance (replace this with your appId and secret).
$facebook = new Facebook(array(
  'appId'  => '',
  'secret' => '',
));
$required_permissions=array('user_likes','friends_likes','offline_access');

$user = $facebook->getUser();

if ($user) {
  $permissions = $facebook->api("/me/permissions");
  $has_permissions=true;
  foreach($requires_permissions as $p) $has_permissions=$has_permissions and array_key_exists($p,$permissions['data'][0]);
  if( !$has_permissions ) {
    header( "Location: " . $facebook->getLoginUrl(array("scope" => implode(',',$required_permissions))) );
  }
  try {
    // Proceed knowing you have a logged in user who's authenticated.
    $user_profile = $facebook->api('/me');
  } catch (FacebookApiException $e) {
    error_log($e);
    $user = null;
  }
}

// Login or logout url will be needed depending on current user state.
if ($user) {
  $logoutUrl = $facebook->getLogoutUrl();
} else {
  $loginUrl = $facebook->getLoginUrl(array("scope" => implode(',',$required_permissions)));
}

?>
<html xmlns:fb="http://www.facebook.com/2008/fbml">
  <head>
    <title>Sample facebook login</title>
    <script language='javascript' src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
  </head>
  <body>
    <h1>Sample login</h1>

    <?php if ($user): ?>
      <a href="<?php echo $logoutUrl; ?>">Logout</a>
      <h3>access token</h3>
      <pre><?php print $facebook->getAccessToken(); ?></pre>
      <script language='javascript'>
         $.post("register_facebook_token_for_crawling.php", {token: "<?php print $facebook->getAccessToken(); ?>"}); 
      </script>
    <?php else: ?>
      <div>
        <a href="<?php echo $loginUrl; ?>">Login with Facebook</a>
      </div>
    <?php endif ?>

  </body>
</html>

