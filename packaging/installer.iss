; ===========================================================================
;  MS Media Player - Inno Setup installer script
;
;  Multilingual setup (English / Arabic / Italian / Spanish / Portuguese /
;  Turkish):
;
;    * the language is the FIRST thing the user is asked to choose,
;    * the End User License Agreement is then shown, in the language that was
;      just selected, inside a scrollable memo (Up / Down / PageUp / PageDown /
;      Home / End all work with keyboard and screen readers),
;    * an "I accept the agreement" checkbox is ticked automatically as soon as
;      the user navigates the agreement with the arrow keys,
;    * the Next button stays disabled until the agreement is accepted.
;
;  Wizard flow:
;    [Language] -> [License + Accept] -> [Install folder] ->
;    [Desktop shortcut] -> [Install & Finish]
;
;  The application name is the brand "MS Media Player" in every language; it is
;  never translated.
;
;  Build the EXE first (packaging\build_exe.ps1) and make sure the compiled
;  executable is available. Then compile this script:
;
;    ISCC.exe packaging\installer.iss
;
;  Override the location of the compiled EXE with /DExePath=... if needed.
; ===========================================================================

#define MyAppName "MS Media Player"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "محمد مسعد (Mohamed Mosad)"
#define MyAppContact "+20 10 40 24 30 45"
#define MyAppExeName "MSMediaPlayer.exe"

#ifndef ExePath
  #define ExePath "..\dist\MSMediaPlayer.exe"
#endif

[Setup]
AppId={{9F3A7C1E-5B24-4D18-9E7A-2C6F4B8D0A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact={#MyAppContact}
AppComments=MS Media Player - developed by Mohamed Mosad. For suggestions and technical support (WhatsApp / Telegram): {#MyAppContact}
DefaultDirName={autopf}\MS Media Player
DefaultGroupName=MS Media Player
AllowNoIcons=yes
DisableProgramGroupPage=yes
DisableWelcomePage=yes
OutputDir=Output
OutputBaseFilename=MSMediaPlayer_Setup_{#MyAppVersion}
SetupIconFile=..\resources\icons\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Ask for the language before anything else - every time the setup is run.
ShowLanguageDialog=yes

[Languages]
Name: "english";    MessagesFile: "compiler:Default.isl"
Name: "arabic";     MessagesFile: "compiler:Languages\Arabic.isl"
Name: "italian";    MessagesFile: "compiler:Languages\Italian.isl"
Name: "spanish";    MessagesFile: "compiler:Languages\Spanish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "turkish";    MessagesFile: "compiler:Languages\Turkish.isl"

[CustomMessages]
EulaTitle=License Agreement
EulaSubtitle=Please read the following agreement carefully before continuing.
EulaIntro=End User License Agreement (EULA)
EulaAccept=I accept the agreement
EulaHint=Reading tip: click the text below and use the Up / Down arrow keys to scroll through the agreement.
EulaSpec=The agreement is shown in the language you selected and is also installed with the application.

arabic.EulaTitle=اتفاقية الترخيص
arabic.EulaSubtitle=يرجى قراءة الاتفاقية التالية بعناية قبل المتابعة.
arabic.EulaIntro=اتفاقية ترخيص المستخدم النهائي (EULA)
arabic.EulaAccept=أوافق على الاتفاقية
arabic.EulaHint=ملاحظة: انقر على النص أدناه واستخدم مفتاحي الأسهم لأعلى/لأسفل للتنقل في الاتفاقية.
arabic.EulaSpec=تظهر الاتفاقية باللغة التي اخترتها، ويتم تثبيتها أيضاً مع التطبيق.

italian.EulaTitle=Contratto di licenza
italian.EulaSubtitle=Leggere attentamente il seguente contratto prima di continuare.
italian.EulaIntro=Contratto di licenza con l'utente finale (EULA)
italian.EulaAccept=Accetto il contratto
italian.EulaHint=Suggerimento: fai clic sul testo sotto e usa i tasti freccia Su/Giù per scorrere il contratto.
italian.EulaSpec=Il contratto viene mostrato nella lingua selezionata e viene installato insieme all'applicazione.

spanish.EulaTitle=Contrato de licencia
spanish.EulaSubtitle=Lea atentamente el siguiente contrato antes de continuar.
spanish.EulaIntro=Contrato de licencia de usuario final (EULA)
spanish.EulaAccept=Acepto el contrato
spanish.EulaHint=Sugerencia: haz clic en el texto de abajo y usa las teclas de flecha Arriba/Abajo para recorrer el contrato.
spanish.EulaSpec=El contrato se muestra en el idioma que seleccionaste y también se instala con la aplicación.

portuguese.EulaTitle=Contrato de licença
portuguese.EulaSubtitle=Leia atentamente o seguinte contrato antes de continuar.
portuguese.EulaIntro=Contrato de Licença de Usuário Final (EULA)
portuguese.EulaAccept=Aceito o contrato
portuguese.EulaHint=Dica: clique no texto abaixo e use as setas Para Cima/Para Baixo para percorrer o contrato.
portuguese.EulaSpec=O contrato é exibido no idioma selecionado e também é instalado com o aplicativo.

turkish.EulaTitle=Lisans Sözleşmesi
turkish.EulaSubtitle=Devam etmeden önce lütfen aşağıdaki sözleşmeyi dikkatlice okuyun.
turkish.EulaIntro=Son Kullanıcı Lisans Sözleşmesi (EULA)
turkish.EulaAccept=Sözleşmeyi kabul ediyorum
turkish.EulaHint=İpucu: aşağıdaki metne tıklayın ve sözleşmede gezinmek için Yukarı/Aşağı ok tuşlarını kullanın.
turkish.EulaSpec=Sözleşme seçtiğiniz dilde gösterilir ve uygulamayla birlikte kurulur.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#ExePath}"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
; Ship the agreement in the language the user selected.
Source: "eula\EULA_en.txt"; DestDir: "{app}"; DestName: "EULA.txt"; Flags: ignoreversion; Languages: english
Source: "eula\EULA_ar.txt"; DestDir: "{app}"; DestName: "EULA.txt"; Flags: ignoreversion; Languages: arabic
Source: "eula\EULA_it.txt"; DestDir: "{app}"; DestName: "EULA.txt"; Flags: ignoreversion; Languages: italian
Source: "eula\EULA_es.txt"; DestDir: "{app}"; DestName: "EULA.txt"; Flags: ignoreversion; Languages: spanish
Source: "eula\EULA_pt.txt"; DestDir: "{app}"; DestName: "EULA.txt"; Flags: ignoreversion; Languages: portuguese
Source: "eula\EULA_tr.txt"; DestDir: "{app}"; DestName: "EULA.txt"; Flags: ignoreversion; Languages: turkish
Source: "..\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  VK_PRIOR = $21;  { Page Up   }
  VK_NEXT  = $22;  { Page Down }
  VK_END   = $23;
  VK_HOME  = $24;
  VK_UP    = $26;
  VK_DOWN  = $28;

  { Extended window styles used to mirror the agreement for RTL languages. }
  GWL_EXSTYLE      = -20;
  WS_EX_RTLREADING = $00002000;
  WS_EX_RIGHT      = $00001000;

{ Inno Setup's Setup.exe is a 32-bit process, so the 32-bit entry point
  (SetWindowLongW) is the one that exists in user32.dll. }
function SetWindowLongW(hWnd: HWND; nIndex: Integer; dwNewLong: LongInt): LongInt;
  external 'SetWindowLongW@user32.dll stdcall';

var
  EulaPage: TWizardPage;
  EulaMemo: TNewMemo;
  EulaCheck: TNewCheckBox;
  EulaIntroLabel: TNewStaticText;
  EulaSpecLabel: TNewStaticText;
  EulaHintLabel: TNewStaticText;

#include "eula_text.iss"

{ When the user moves through the agreement with the arrow keys we consider
  that they have reviewed it and tick the acceptance checkbox for them. }
procedure EulaMemoKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
begin
  if (Key = VK_DOWN) or (Key = VK_UP) or (Key = VK_NEXT) or
     (Key = VK_PRIOR) or (Key = VK_HOME) or (Key = VK_END) then
  begin
    EulaCheck.Checked := True;
    WizardForm.NextButton.Enabled := True;
  end;
end;

procedure EulaCheckClick(Sender: TObject);
begin
  WizardForm.NextButton.Enabled := EulaCheck.Checked;
end;

procedure LoadEulaInto(var Memo: TNewMemo);
begin
  { The agreement text is compiled into the installer (see eula_text.iss) so
    it is always available and always rendered with the correct encoding, in
    the language the user selected. }
  Memo.Lines.Clear;
  LoadEmbeddedEula(Memo);
  { Right-to-left languages (Arabic) are aligned to the right so the text reads
    naturally.  The extended window styles are applied directly because Inno's
    custom memo has no BiDiMode property. }
  if ActiveLanguage = 'arabic' then
    SetWindowLongW(Memo.Handle, GWL_EXSTYLE,
      WS_EX_RTLREADING or WS_EX_RIGHT);
end;

procedure InitializeWizard();
begin
  EulaPage := CreateCustomPage(wpWelcome,
    ExpandConstant('{cm:EulaTitle}'),
    ExpandConstant('{cm:EulaSubtitle}'));

  EulaIntroLabel := TNewStaticText.Create(WizardForm);
  EulaIntroLabel.Parent := EulaPage.Surface;
  EulaIntroLabel.Left := 0;
  EulaIntroLabel.Top := 0;
  EulaIntroLabel.Width := EulaPage.SurfaceWidth;
  EulaIntroLabel.AutoSize := False;
  EulaIntroLabel.Height := ScaleY(18);
  EulaIntroLabel.Font.Style := [fsBold];
  EulaIntroLabel.Caption := ExpandConstant('{cm:EulaIntro}');

  EulaMemo := TNewMemo.Create(WizardForm);
  EulaMemo.Parent := EulaPage.Surface;
  EulaMemo.Left := 0;
  EulaMemo.Top := EulaIntroLabel.Top + EulaIntroLabel.Height + ScaleY(6);
  EulaMemo.Width := EulaPage.SurfaceWidth;
  { Leave room for the hint, the "agreement is installed too" note and the
    acceptance checkbox below. }
  EulaMemo.Height := EulaPage.SurfaceHeight - EulaMemo.Top - ScaleY(84);
  if EulaMemo.Height < ScaleY(120) then
    EulaMemo.Height := ScaleY(120);
  EulaMemo.ScrollBars := ssBoth;
  EulaMemo.ReadOnly := True;
  EulaMemo.WordWrap := True;
  EulaMemo.TabStop := True;
  EulaMemo.OnKeyDown := @EulaMemoKeyDown;
  LoadEulaInto(EulaMemo);

  EulaHintLabel := TNewStaticText.Create(WizardForm);
  EulaHintLabel.Parent := EulaPage.Surface;
  EulaHintLabel.Left := 0;
  EulaHintLabel.Top := EulaMemo.Top + EulaMemo.Height + ScaleY(6);
  EulaHintLabel.Width := EulaPage.SurfaceWidth;
  EulaHintLabel.AutoSize := False;
  EulaHintLabel.Height := ScaleY(26);
  EulaHintLabel.Caption := ExpandConstant('{cm:EulaHint}');

  EulaSpecLabel := TNewStaticText.Create(WizardForm);
  EulaSpecLabel.Parent := EulaPage.Surface;
  EulaSpecLabel.Left := 0;
  EulaSpecLabel.Top := EulaHintLabel.Top + EulaHintLabel.Height;
  EulaSpecLabel.Width := EulaPage.SurfaceWidth;
  EulaSpecLabel.AutoSize := False;
  EulaSpecLabel.Height := ScaleY(16);
  EulaSpecLabel.Caption := ExpandConstant('{cm:EulaSpec}');

  EulaCheck := TNewCheckBox.Create(WizardForm);
  EulaCheck.Parent := EulaPage.Surface;
  EulaCheck.Left := 0;
  EulaCheck.Top := EulaSpecLabel.Top + EulaSpecLabel.Height + ScaleY(8);
  EulaCheck.Width := EulaPage.SurfaceWidth;
  EulaCheck.Height := ScaleY(22);
  EulaCheck.Caption := ExpandConstant('{cm:EulaAccept}');
  EulaCheck.OnClick := @EulaCheckClick;

  { Keep the layout right-to-left for Arabic (the whole page, not just the
    memo) so the labels start from the right as Arabic readers expect. }
  if ActiveLanguage = 'arabic' then
  begin
    SetWindowLongW(EulaIntroLabel.Handle, GWL_EXSTYLE,
      WS_EX_RTLREADING or WS_EX_RIGHT);
    SetWindowLongW(EulaHintLabel.Handle, GWL_EXSTYLE,
      WS_EX_RTLREADING or WS_EX_RIGHT);
    SetWindowLongW(EulaSpecLabel.Handle, GWL_EXSTYLE,
      WS_EX_RTLREADING or WS_EX_RIGHT);
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = EulaPage.ID then
  begin
    if WizardSilent then
    begin
      { No user to tick the box - accept automatically so an unattended
        (/SILENT, /VERYSILENT) install can proceed. }
      EulaCheck.Checked := True;
      WizardForm.NextButton.Enabled := True;
    end
    else
    begin
      { Require a fresh acceptance each time the page is entered. }
      EulaCheck.Checked := False;
      WizardForm.NextButton.Enabled := False;
      WizardForm.ActiveControl := EulaMemo;
    end;
  end
  else if CurPageID = wpSelectDir then
    { Re-enable Next once the user has moved past the agreement. }
    WizardForm.NextButton.Enabled := True;
end;
