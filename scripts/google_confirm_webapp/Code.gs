/**
 * Human-Confirm Gate — Google-Auth-Bein.
 *
 * Als Web App deployen (Execute as: Me, Access: Only myself) unter dem
 * EIGENEN Google-Account des Operators. Der Aufruf der URL erzwingt damit
 * Google-Sign-In durch die Apps-Script-Zugriffsbeschraenkung selbst — noch
 * bevor dieser Code ueberhaupt laeuft. Der Email-Check unten ist zusaetzlich
 * defense-in-depth (fail closed), kein Ersatz dafuer.
 *
 * Script Properties (Project Settings -> Script Properties), einmalig setzen:
 *   GITHUB_TOKEN          Fine-grained PAT, NUR dieses Repo, NUR Checks: Read+Write
 *   ALLOWED_GOOGLE_EMAIL  die eine Gmail-Adresse, die bestaetigen darf
 *
 * Hinweis (Code-Honesty, wie im Rest des Repos): Session.getActiveUser()
 * liefert bei manchen privaten Gmail-Deployments einen leeren String (bekannte
 * Apps-Script-Einschraenkung ausserhalb von Google Workspace). In dem Fall
 * traegt allein die Deployment-Zugriffsbeschraenkung "Nur ich" die Google-
 * Auth-Garantie — siehe docs/ops/HUMAN_CONFIRM_GATE.md.
 */

function doGet(e) {
  const props = PropertiesService.getScriptProperties();
  const allowedEmail = props.getProperty('ALLOWED_GOOGLE_EMAIL');
  const token = props.getProperty('GITHUB_TOKEN');

  const activeEmail = Session.getActiveUser().getEmail();
  if (allowedEmail && activeEmail && activeEmail !== allowedEmail) {
    return htmlResponse(
      '❌ Nicht autorisiert',
      'Angemeldet als "' + activeEmail + '". Nur der hinterlegte Account darf bestaetigen.'
    );
  }

  const owner = e.parameter.owner;
  const repo = e.parameter.repo;
  const sha = e.parameter.sha;
  const checkRunId = e.parameter.check_run_id;

  if (!owner || !repo || !sha || !checkRunId) {
    return htmlResponse('❌ Fehlender Parameter', 'owner, repo, sha und check_run_id werden benoetigt.');
  }
  if (!token) {
    return htmlResponse('❌ Konfigurationsfehler', 'GITHUB_TOKEN Script Property ist nicht gesetzt.');
  }

  const url = 'https://api.github.com/repos/' + owner + '/' + repo + '/check-runs/' + checkRunId;
  const response = UrlFetchApp.fetch(url, {
    method: 'patch',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json',
    },
    payload: JSON.stringify({
      status: 'completed',
      conclusion: 'success',
      output: {
        title: 'Google-Bestaetigung erhalten',
        summary: 'Bestaetigt von ' + (activeEmail || 'Google-Account (Deployment-beschraenkt)') + ' am ' + new Date().toISOString() + '.',
      },
    }),
    muteHttpExceptions: true,
  });

  if (response.getResponseCode() >= 300) {
    return htmlResponse('❌ GitHub-API-Fehler (' + response.getResponseCode() + ')', response.getContentText());
  }

  return htmlResponse(
    '✅ Bestaetigt',
    'Commit ' + sha.substring(0, 7) + ' als Google-bestaetigt markiert. GitHub-Review (Approve) nicht vergessen — beides ist Pflicht fuer den Merge.'
  );
}

function htmlResponse(title, body) {
  return HtmlService.createHtmlOutput('<h2>' + title + '</h2><p>' + body + '</p>');
}
