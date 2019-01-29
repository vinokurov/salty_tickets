import itertools
import json

import requests
from salty_tickets import config
from salty_tickets.config import MONGO, EMAIL_FROM
from salty_tickets.dao import TicketsDAO
from salty_tickets.models.registrations import Person
from salty_tickets.tokens import RegistrationToken

HTML_TOP = """
<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">

<head>
  <title> </title>
  <!--[if !mso]><!-- -->
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <!--<![endif]-->
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style type="text/css">
    #outlook a {
      padding: 0;
    }

    .ReadMsgBody {
      width: 100%;
    }

    .ExternalClass {
      width: 100%;
    }

    .ExternalClass * {
      line-height: 100%;
    }

    body {
      margin: 0;
      padding: 0;
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }

    table,
    td {
      border-collapse: collapse;
      mso-table-lspace: 0pt;
      mso-table-rspace: 0pt;
    }

    img {
      border: 0;
      height: auto;
      line-height: 100%;
      outline: none;
      text-decoration: none;
      -ms-interpolation-mode: bicubic;
    }

    p {
      display: block;
      margin: 13px 0;
    }
  </style>
  <!--[if !mso]><!-->
  <style type="text/css">
    @media only screen and (max-width:480px) {
      @-ms-viewport {
        width: 320px;
      }
      @viewport {
        width: 320px;
      }
    }
  </style>
  <!--<![endif]-->
  <!--[if mso]>
        <xml>
        <o:OfficeDocumentSettings>
          <o:AllowPNG/>
          <o:PixelsPerInch>96</o:PixelsPerInch>
        </o:OfficeDocumentSettings>
        </xml>
        <![endif]-->
  <!--[if lte mso 11]>
        <style type="text/css">
          .outlook-group-fix { width:100% !important; }
        </style>
        <![endif]-->
  <!--[if !mso]><!-->
  <link href="https://fonts.googleapis.com/css?family=Raleway" rel="stylesheet" type="text/css">
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans+TC:900" rel="stylesheet" type="text/css">
  <style type="text/css">
    @import url(https://fonts.googleapis.com/css?family=Raleway);
    @import url(https://fonts.googleapis.com/css?family=Noto+Sans+TC:900);
  </style>
  <!--<![endif]-->
  <style type="text/css">
    @media only screen and (min-width:480px) {
      .mj-column-per-100 {
        width: 100% !important;
        max-width: 100%;
      }
      .mj-column-per-50 {
        width: 50% !important;
        max-width: 50%;
      }
    }
  </style>
  <style type="text/css">
    @media only screen and (max-width:480px) {
      table.full-width-mobile {
        width: 100% !important;
      }
      td.full-width-mobile {
        width: auto !important;
      }
    }
  </style>
</head>

<body>
  <div style="">
    <!--[if mso | IE]>
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="background:#1B4F72;background-color:#1B4F72;Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#1B4F72;background-color:#1B4F72;width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:600px;"
            >
          <![endif]-->
              <div class="mj-column-per-100 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="center" style="font-size:0px;padding:10px 25px;padding-top:5px;padding-bottom:0px;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:25px;line-height:1;text-align:center;color:#fff;"> MIND THE SHAG </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="center" style="font-size:0px;padding:10px 25px;padding-top:5px;padding-bottom:0;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:10px;line-height:1;text-align:center;color:#fff;"> London SHAG Festival </div>
                    </td>
                  </tr>
                  <tr>
                    <td style="font-size:0px;padding:10px 25px;padding-top:3px;padding-bottom:0px;word-break:break-word;">
                      <p style="border-top:solid 1px #fff;font-size:1;margin:0px auto;width:120px;"> </p>
                      <!--[if mso | IE]>
        <table
           align="center" border="0" cellpadding="0" cellspacing="0" style="border-top:solid 1px #fff;font-size:1;margin:0px auto;width:120px;" role="presentation" width="120px"
        >
          <tr>
            <td style="height:0;line-height:0;">
              &nbsp;
            </td>
          </tr>
        </table>
      <![endif]-->
                    </td>
                  </tr>
                  <tr>
                    <td align="center" style="font-size:0px;padding:10px 25px;padding-top:3px;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:10px;line-height:1;text-align:center;color:#fff;"> 29-31 March 2019 </div>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:600px;"
            >
          <![endif]-->
              <div class="mj-column-per-100 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <div style="font-family:Raleway;font-size:13px;line-height:1;text-align:left;color:#000000;">

"""

HTML_HELLO_1_STATION = """
                        <p>Dear %recipient.full_name%,</p>
                        <p>Did you know that there is a special offer that you may find interesting?</p>
                        <p>As you have a Full Pass, you can <b>book this new station for just £15</b>. The offer will expire when the class reaches 15 people. Yet if the station doesn't reach it's minimum until this Wednesday we will need to cancel it.</p>
"""

HTML_HELLO_2_STATIONS = """
                        <p>Dear %recipient.full_name%,</p>
                        <p>Did you know that there is a special offer that you may find interesting?</p>
                        <p>As you have a Full Pass, you can <b>book any of these new stations for just £15</b>. The offer will expire when a class reaches 15 people. Yet if a station doesn't reach it's minimum until this Wednesday we will need to cancel it.</p>
"""

HTML_MIDDLE = """
                      </div>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:600px;"
            >
          <![endif]-->
              <div class="mj-column-per-100 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="center" vertical-align="middle" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:separate;line-height:100%;">
                        <tr>
                          <td align="center" bgcolor="#1B4F72" role="presentation" style="border:none;border-radius:3px;cursor:auto;padding:10px 25px;" valign="middle"> <a href="https://www.saltyjitterbugs.co.uk/register/mind_the_shag_2019?reg_token=%recipient.reg_token%" style="background:#1B4F72;color:white;font-family:Noto Sans TC;font-size:13px;font-weight:normal;line-height:120%;Margin:0;text-decoration:none;text-transform:none;"
                              target="_blank">
              Book for just £15
            </a> </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      <![endif]-->
"""

HTML_SHAG_DYNAMITE = """
    <!-- SHAG DYNAMITE -->
    <!--[if mso | IE]>
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:300px;"
            >
          <![endif]-->
              <div class="mj-column-per-50 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-bottom:0;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:20px;line-height:1;text-align:left;color:#626262;"> SHAG DYNAMITE </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-top:2px;padding-bottom:0;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:12px;line-height:1;text-align:left;color:#626262;"> Lasrissa & Heiko </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-top:10px;padding-bottom:0;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:12px;line-height:1;text-align:left;color:red;"> Collegiate Shag Veteran </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-top:15px;word-break:break-word;">
                      <div style="font-family:Raleway;font-size:10px;line-height:1;text-align:left;color:#000000;"> Sunday 31-March, 14:00-16:00 </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <div style="font-family:Raleway;font-size:13px;line-height:1;text-align:left;color:#000000;"> Looking for more power moves for competitions, performances or to spice up your social Shag? In this station Larissa & Heiko, the Jitterbugs from Basel, who have competed in almost every major Shag event in the world, are going to
                        share their favourite killer moves! </div>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
            <td
               class="" style="vertical-align:top;width:300px;"
            >
          <![endif]-->
              <div class="mj-column-per-50 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="center" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:collapse;border-spacing:0px;">
                        <tbody>
                          <tr>
                            <td style="width:200px;"> <img height="auto" src="https://static.wixstatic.com/media/eb4a35_d6c7be988eee4e9d867d127442cd4ce7~mv2_d_2362_3543_s_2.jpg/v1/fill/w_206,h_280,al_c,q_80,usm_0.66_1.00_0.01/HL_couple3.webp" style="border:0;display:block;outline:none;text-decoration:none;height:auto;width:100%;"
                                width="200" /> </td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      <![endif]-->
"""

HTML_SOLO_SHAG = """
    <!-- SOLO SHAG -->
    <!--[if mso | IE]>
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:300px;"
            >
          <![endif]-->
              <div class="mj-column-per-50 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-bottom:0;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:20px;line-height:1;text-align:left;color:#626262;"> SOLO SHAG </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-top:2px;padding-bottom:0;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:12px;line-height:1;text-align:left;color:#626262;"> Cherry & Filip </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-top:10px;padding-bottom:0;word-break:break-word;">
                      <div style="font-family:Noto Sans TC;font-size:12px;line-height:1;text-align:left;color:#0033cc;"> Collegiate Shag </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-top:15px;word-break:break-word;">
                      <div style="font-family:Raleway;font-size:10px;line-height:1;text-align:left;color:#000000;"> Sunday 31-March, 16:30-18:30 </div>
                    </td>
                  </tr>
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <div style="font-family:Raleway;font-size:13px;line-height:1;text-align:left;color:#000000;"> Join the latest trend in the Shag community all over the world! As well as being great fun to dance alone, Solo Shag will also enhance your partner dancing by building your confidence in developing your own personal variations; great
                        for leaders and followers alike! In this station with Cherry and Filip, the pioneers of the style, you will work both solo and in couples. You will learn a 1-minute choreography that will be performed later at the party. </div>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
            <td
               class="" style="vertical-align:top;width:300px;"
            >
          <![endif]-->
              <div class="mj-column-per-50 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="center" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:collapse;border-spacing:0px;">
                        <tbody>
                          <tr>
                            <td style="width:200px;"> <img height="auto" src="https://static.wixstatic.com/media/eb4a35_ed1ce697937b4d6fbb6c8d295958421b~mv2_d_5264_3509_s_4_2.jpg/v1/fill/w_206,h_280,al_c,q_80,usm_0.66_1.00_0.01/CH_couple2.webp" style="border:0;display:block;outline:none;text-decoration:none;height:auto;width:100%;"
                                width="200" /> </td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      <![endif]-->
"""

HTML_BOTTOM = """
    <!--[if mso | IE]>
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:600px;"
            >
          <![endif]-->
              <div class="mj-column-per-100 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="center" vertical-align="middle" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:separate;line-height:100%;">
                        <tr>
                          <td align="center" bgcolor="#1B4F72" role="presentation" style="border:none;border-radius:3px;cursor:auto;padding:10px 25px;" valign="middle"> <a href="https://www.saltyjitterbugs.co.uk/register/mind_the_shag_2019?reg_token=%recipient.reg_token%" style="background:#1B4F72;color:white;font-family:Noto Sans TC;font-size:13px;font-weight:normal;line-height:120%;Margin:0;text-decoration:none;text-transform:none;"
                              target="_blank">
              Book for just £15
            </a> </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:20px 0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:600px;"
            >
          <![endif]-->
              <div class="mj-column-per-100 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <div style="font-family:Raleway;font-size:13px;line-height:1;text-align:left;color:#000000;"> Thank you,<br/> Mind the Shag Team </div>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               class="" style="vertical-align:top;width:600px;"
            >
          <![endif]-->
              <div class="mj-column-per-100 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;word-break:break-word;">
                      <div style="font-family:Raleway;font-size:8px;line-height:1;text-align:left;color:#000000;"> If you don't want to receive email news from Mind the Shag 2019, please click <a href="https://www.saltyjitterbugs.co.uk/unsubscribe_email/%recipient.reg_token%">unsubscribe</a>. </div>
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      
      <table
         align="center" border="0" cellpadding="0" cellspacing="0" class="" style="width:600px;" width="600"
      >
        <tr>
          <td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;">
      <![endif]-->
    <div style="background:#000;background-color:#000;Margin:0px auto;max-width:600px;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#000;background-color:#000;width:100%;">
        <tbody>
          <tr>
            <td style="direction:ltr;font-size:0px;padding:0;text-align:center;vertical-align:top;">
              <!--[if mso | IE]>
                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                
        <tr>
      
            <td
               align="left" class="" style="vertical-align:top;width:600px;"
            >
          <![endif]-->
              <div class="mj-column-per-100 outlook-group-fix" style="font-size:13px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;">
                <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%">
                  <tr>
                    <td align="left" style="font-size:0px;padding:10px 25px;padding-top:0px;padding-bottom:0px;word-break:break-word;">
                      <!--[if mso | IE]>
      <table
         align="left" border="0" cellpadding="0" cellspacing="0" role="presentation"
      >
        <tr>
      
              <td>
            <![endif]-->
                      <table align="left" border="0" cellpadding="0" cellspacing="0" role="presentation" style="float:none;display:inline-table;">
                        <tr>
                          <td style="padding:4px;">
                            <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#1B4F72;border-radius:3px;width:14px;">
                              <tr>
                                <td style="font-size:0;height:14px;vertical-align:middle;width:14px;"> <a href="http://mindtheshag.co.uk" target="_blank">
                    <img
                       height="14" src="https://static.wixstatic.com/media/eb4a35_bb28b405c8ae49d498b45b5cce62ef70~mv2.jpg/v1/fill/w_32%2Ch_32%2Clg_1%2Cusm_0.66_1.00_0.01/eb4a35_bb28b405c8ae49d498b45b5cce62ef70~mv2.jpg" style="border-radius:3px;" width="14"
                    />
                  </a> </td>
                              </tr>
                            </table>
                          </td>
                          <td style="vertical-align:middle;padding:4px 4px 4px 0;"> <a href="http://mindtheshag.co.uk" style="color:white;font-size:8px;font-family:Raleway;line-height:22px;text-decoration:none;">
              http://mindtheshag.co.uk
            </a> </td>
                        </tr>
                      </table>
                      <!--[if mso | IE]>
              </td>
            
              <td>
            <![endif]-->
                      <table align="left" border="0" cellpadding="0" cellspacing="0" role="presentation" style="float:none;display:inline-table;">
                        <tr>
                          <td style="padding:4px;">
                            <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#1B4F72;border-radius:3px;width:14px;">
                              <tr>
                                <td style="font-size:0;height:14px;vertical-align:middle;width:14px;"> <a href="https://www.facebook.com/mindtheshag" target="_blank">
                    <img
                       height="14" src="https://www.mailjet.com/images/theme/v1/icons/ico-social/facebook.png" style="border-radius:3px;" width="14"
                    />
                  </a> </td>
                              </tr>
                            </table>
                          </td>
                          <td style="vertical-align:middle;padding:4px 4px 4px 0;"> <a href="https://www.facebook.com/mindtheshag" style="color:white;font-size:8px;font-family:Raleway;line-height:22px;text-decoration:none;">
              Facebook
            </a> </td>
                        </tr>
                      </table>
                      <!--[if mso | IE]>
              </td>
            
              <td>
            <![endif]-->
                      <table align="left" border="0" cellpadding="0" cellspacing="0" role="presentation" style="float:none;display:inline-table;">
                        <tr>
                          <td style="padding:4px;">
                            <table border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#f00;border-radius:3px;width:14px;">
                              <tr>
                                <td style="font-size:0;height:14px;vertical-align:middle;width:14px;"> <a href="https://www.youtube.com/channel/UCY1bkFZP8wCHPGM3Ajg5AyQ" target="_blank">
                    <img
                       height="14" src="https://www.mailjet.com/images/theme/v1/icons/ico-social/youtube.png" style="border-radius:3px;" width="14"
                    />
                  </a> </td>
                              </tr>
                            </table>
                          </td>
                          <td style="vertical-align:middle;padding:4px 4px 4px 0;"> <a href="https://www.youtube.com/channel/UCY1bkFZP8wCHPGM3Ajg5AyQ" style="color:white;font-size:8px;font-family:Raleway;line-height:22px;text-decoration:none;">
              Youtube
            </a> </td>
                        </tr>
                      </table>
                      <!--[if mso | IE]>
              </td>
            
          </tr>
        </table>
      <![endif]-->
                    </td>
                  </tr>
                </table>
              </div>
              <!--[if mso | IE]>
            </td>
          
        </tr>
      
                  </table>
                <![endif]-->
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--[if mso | IE]>
          </td>
        </tr>
      </table>
      <![endif]-->
  </div>
</body>

</html>
"""


def get_html(solo_shag=False, shag_dynamite=False):
    html_body = HTML_TOP
    if solo_shag and shag_dynamite:
        html_body += HTML_HELLO_2_STATIONS
    else:
        html_body += HTML_HELLO_1_STATION

    html_body += HTML_MIDDLE

    if shag_dynamite:
        html_body += HTML_SHAG_DYNAMITE

    if solo_shag:
        html_body += HTML_SOLO_SHAG

    html_body += HTML_BOTTOM
    return html_body


def person_vars(person: Person):
    return dict(
        full_name=person.full_name,
        reg_token=RegistrationToken().serialize(person)
    )


def persons_list_to_vars_dict(persons):
    return {p.email: person_vars(p) for p in persons}


def ticket_persons(event, ticket_key):
    return set([
        r.person for r in event.tickets[ticket_key].registrations
        if r.person == r.registered_by and r.active
    ])


def get_person_lists():
    dao = TicketsDAO(host=MONGO)
    event_key = 'mind_the_shag_2019'
    event = dao.get_event_by_key(event_key)
    # email_settings = dao.get_event_email_settings(event_key)

    advanced_stations = {
        'creme_de_la_creme_shag',
        'showmans_shag',
        'fast_furious_shag',
        'shag_clinic'
    }
    sunday_16 = {'shag_roller_coaster', 'shag_hall_of_fame'}
    sunday_18 = {'millionaire_shag', 'shag_boomerang'}

    full_pass_persons = ticket_persons(event, 'full_pass')
    advanced_persons = set(itertools.chain.from_iterable([
        ticket_persons(event, key) for key in advanced_stations
    ]))
    sunday_16_persons = set(itertools.chain.from_iterable([
        ticket_persons(event, key) for key in sunday_16
    ]))
    sunday_18_persons = set(itertools.chain.from_iterable([
        ticket_persons(event, key) for key in sunday_18
    ]))

    persons_4_dynamite = full_pass_persons & advanced_persons - sunday_16_persons
    persons_4_solo = full_pass_persons - sunday_18_persons

    persons_4_dynamite_only = persons_4_dynamite - persons_4_solo
    persons_4_solo_only = persons_4_solo - persons_4_dynamite
    persons_4_both = persons_4_dynamite & persons_4_solo

    return (
        persons_list_to_vars_dict(persons_4_dynamite_only),
        persons_list_to_vars_dict(persons_4_solo_only),
        persons_list_to_vars_dict(persons_4_both)
    )


def send_mailing_list(subject, html_body, vars):
    email_data = {
        'from': EMAIL_FROM,
        'to': vars.keys(),
        'subject': subject,
        'text': None,
        'html': html_body,
        'recipient-variables': json.dumps(vars),
    }
    if not config.MODE_TESTING:
        email_data['bcc'] = config.EMAIL_DEBUG
    result = requests.post('https://api.mailgun.net/v3/saltyjitterbugs.co.uk/messages',
                           auth=('api', config.MAILGUN_KEY),
                           data=email_data,
                           files=None)
    return result


SUBJECT = 'Mind the Shag - New Stations'


def main():
    vars_dynamite, vars_solo, vars_both = get_person_lists()
    send_mailing_list(SUBJECT, get_html(solo_shag=False, shag_dynamite=True), vars_dynamite)
    send_mailing_list(SUBJECT, get_html(solo_shag=True, shag_dynamite=False), vars_solo)
    send_mailing_list(SUBJECT, get_html(solo_shag=True, shag_dynamite=True), vars_both)


if __name__ == '__main__':
    main()
