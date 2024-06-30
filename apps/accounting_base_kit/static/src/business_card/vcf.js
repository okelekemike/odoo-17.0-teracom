'use strict';

function downloadToFile(content, filename, contentType) {
  const a = document.createElement('a');
  const file = new Blob([content], { type: contentType });

  a.href = URL.createObjectURL(file);
  a.download = filename;
  a.click();

  URL.revokeObjectURL(a.href);
}

function previewFile(event) {
  let reader = new FileReader();
  let file = event.target.files[0];

  reader.readAsDataURL(file);
  reader.onloadend = () => (previewEl.src = reader.result);
}

const makeVCardVersion = () => `VERSION:3.0`;
const makeVCardInfo = (info) => `N;CHARSET=UTF-8:${info}`;
const makeVCardName = (name) => `N;CHARSET=UTF-8:${name}`;
const makeVCardOrg = (org) => `ORG:${org}`;
const makeVCardTitle = (title) => `TITLE:${title}`;
const makeVCardPhoto = (img) => `PHOTO;TYPE=JPEG;ENCODING=b:[${img}]`;
const makeVCardTel = (phone) => `TEL;TYPE=WORK,VOICE:${phone}`;
const makeVCardAdr = (address) => `ADR;TYPE=WORK,PREF:;;${address}`;
const makeVCardEmail = (email) => `EMAIL:${email}`;
const makeVCardTimeStamp = () => `REV:${new Date().toISOString()}`;

function makeVCard() {
  let vcard = `BEGIN:VCARD
VERSION:3.0
N;CHARSET=UTF-8:${vcf_lastname.value};${vcf_middlename.value};${vcf_firstname.value}
FN;CHARSET=UTF-8:${vcf_firstname.value} ${vcf_middlename.value} ${vcf_lastname.value}
TEL;WORK:${vcf_phone.value}
ADR;CHARSET=UTF-8;WORK:;;${vcf_street.value} ${vcf_street2.value};${vcf_city.value};${vcf_state.value};${vcf_zip.value};${vcf_country.value}
EMAIL;WORK:${vcf_email.value}
URL;WORK:${vcf_website.value}
TITLE;CHARSET=UTF-8:${vcf_job_title.value}
ORG;CHARSET=UTF-8:${vcf_company_name.value}
NOTE: P.IVA: ${vcf_company_vat.value}
END:VCARD`;
  let file_name=`${vcf_name.value}`+".vcf";
  downloadToFile(vcard, file_name, 'text/vcard');
}

downloadVCF.addEventListener('click', makeVCard);
fileVCF.addEventListener('change', previewFile);
